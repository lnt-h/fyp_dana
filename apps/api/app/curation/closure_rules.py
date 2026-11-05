"""Curator-reviewed calendar rules (DEC-016, ADR-011 0.3). AI never writes here.

``params`` is validated per ``rule_kind`` by the Pydantic models below (the DB only checks
that it is an object), so Plan Health can trust approved rows.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import (
    audit,
    commit,
    default_city_id,
    flush,
    get_place,
    require_city,
    require_source_revisions,
)
from app.errors import conflict, invalid, not_found
from app.models.catalog import PlaceClosureRule
from app.models.reference import Area
from app.schemas.admin import ClosureRule, ClosureRuleCreate, ClosureRuleList, ClosureRuleUpdate

_HHMM = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"
_MMDD = r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"


class _Params(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WeeklyParams(_Params):
    weekdays: list[int] = Field(min_length=1, max_length=7)
    from_: str | None = Field(default=None, alias="from", pattern=_HHMM)
    to: str | None = Field(default=None, pattern=_HHMM)

    @field_validator("weekdays")
    @classmethod
    def _iso_weekdays(cls, value: list[int]) -> list[int]:
        if any(day < 1 or day > 7 for day in value) or len(set(value)) != len(value):
            raise ValueError("weekdays are unique ISO days 1..7 (1 = Monday)")
        return value

    @model_validator(mode="after")
    def _window(self) -> WeeklyParams:
        if (self.from_ is None) != (self.to is None):
            raise ValueError("from and to go together")
        return self


class DateParams(_Params):
    dates: list[date] | None = Field(default=None, min_length=1, max_length=366)
    month_day: list[str] | None = Field(default=None, min_length=1, max_length=366)

    @field_validator("month_day")
    @classmethod
    def _month_days(cls, value: list[str] | None) -> list[str] | None:
        if value is not None and not all(re.fullmatch(_MMDD, item) for item in value):
            raise ValueError("month_day items are MM-DD")
        return value

    @model_validator(mode="after")
    def _exactly_one(self) -> DateParams:
        if (self.dates is None) == (self.month_day is None):
            raise ValueError("give exactly one of dates or month_day")
        return self


class LunarDateParams(_Params):
    lunar_days: list[int] = Field(min_length=1, max_length=30)
    lunar_months: list[int] | None = Field(default=None, min_length=1, max_length=12)

    @model_validator(mode="after")
    def _ranges(self) -> LunarDateParams:
        if any(day < 1 or day > 30 for day in self.lunar_days):
            raise ValueError("lunar_days are 1..30")
        if self.lunar_months is not None and any(m < 1 or m > 12 for m in self.lunar_months):
            raise ValueError("lunar_months are 1..12")
        return self


class SeasonParams(_Params):
    from_month_day: str = Field(pattern=_MMDD)
    to_month_day: str = Field(pattern=_MMDD)


class TicketValidityParams(_Params):
    valid_same_day: Literal[True] | None = None
    valid_hours: int | None = Field(default=None, ge=1, le=168)

    @model_validator(mode="after")
    def _exactly_one(self) -> TicketValidityParams:
        if (self.valid_same_day is None) == (self.valid_hours is None):
            raise ValueError("give exactly one of valid_same_day or valid_hours")
        return self


PARAMS_BY_KIND: dict[str, type[_Params]] = {
    "WEEKLY": WeeklyParams,
    "DATE": DateParams,
    "LUNAR_DATE": LunarDateParams,
    "SEASON": SeasonParams,
    "TICKET_VALIDITY": TicketValidityParams,
}


def validate_params(rule_kind: str, params: dict[str, Any]) -> dict[str, Any]:
    """Return the canonical JSON params for ``rule_kind`` or raise 422 ``invalid_rule_params``."""
    model = PARAMS_BY_KIND[rule_kind]
    try:
        parsed = model.model_validate(params)
    except ValidationError as exc:
        fields = [
            {"location": list(error["loc"]), "message": error["msg"]} for error in exc.errors()
        ]
        raise invalid(
            "invalid_rule_params",
            f"params do not match rule_kind {rule_kind}",
            rule_kind=rule_kind,
            fields=fields,
        ) from exc
    return parsed.model_dump(mode="json", by_alias=True, exclude_none=True)


def default_severity(effect: str) -> str:
    return "BLOCKING" if effect == "CLOSED" else "WARNING"


class ClosureRuleService:
    def __init__(self, session: AsyncSession, *, default_city_code: str) -> None:
        self._session = session
        self._default_city_code = default_city_code

    async def list_rules(
        self,
        *,
        place_id: uuid.UUID | None = None,
        city_id: uuid.UUID | None = None,
        area_code: str | None = None,
        applies_to: str | None = None,
        review_state: str | None = None,
    ) -> ClosureRuleList:
        statement = select(PlaceClosureRule)
        if place_id is not None:
            await get_place(self._session, place_id)
            statement = statement.where(PlaceClosureRule.place_id == place_id)
        if city_id is not None:
            statement = statement.where(PlaceClosureRule.city_id == city_id)
        if area_code is not None:
            statement = statement.where(PlaceClosureRule.area_code == area_code)
        if applies_to is not None:
            statement = statement.where(PlaceClosureRule.applies_to == applies_to)
        if review_state is not None:
            statement = statement.where(PlaceClosureRule.review_state == review_state)
        rows = (
            await self._session.scalars(
                statement.order_by(PlaceClosureRule.created_at.desc(), PlaceClosureRule.id)
            )
        ).all()
        return ClosureRuleList(items=[to_schema(row) for row in rows])

    async def get_rule(self, rule_id: uuid.UUID) -> ClosureRule:
        return to_schema(await self._rule(rule_id))

    async def create_rule(
        self,
        data: ClosureRuleCreate,
        actor_account_id: uuid.UUID,
        *,
        place_id: uuid.UUID | None = None,
    ) -> ClosureRule:
        if place_id is not None:
            if data.applies_to != "PLACE" or data.area_code is not None:
                raise invalid(
                    "invalid_rule_target", "Place rules have applies_to PLACE and no area_code"
                )
            place = await get_place(self._session, place_id)
            city_id = place.city_id
            area_code = None
        else:
            if data.applies_to == "PLACE":
                raise invalid(
                    "invalid_rule_target",
                    "Create PLACE rules under /admin/places/{place_id}/closure-rules",
                )
            city_id = data.city_id or await default_city_id(self._session, self._default_city_code)
            await require_city(self._session, city_id)
            area_code = data.area_code if data.applies_to == "AREA" else None
            if data.applies_to == "AREA":
                await self._require_area(area_code, city_id)
            elif data.area_code is not None:
                raise invalid("invalid_rule_target", "CITY rules have no area_code")
        _check_range(data.effective_from, data.effective_to)
        params = validate_params(data.rule_kind, data.params)
        if data.source_revision_id is not None:
            await require_source_revisions(self._session, [data.source_revision_id])
        row = PlaceClosureRule(
            city_id=city_id,
            applies_to=data.applies_to,
            place_id=place_id,
            area_code=area_code,
            rule_kind=data.rule_kind,
            effect=data.effect,
            params=params,
            severity=data.severity or default_severity(data.effect),
            note_vi=data.note_vi,
            note_en=data.note_en,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            source_revision_id=data.source_revision_id,
            review_state="DRAFT",
        )
        self._session.add(row)
        await flush(self._session)
        self._audit(actor_account_id, row, "create", None)
        await commit(self._session)
        await self._session.refresh(row)
        return to_schema(row)

    async def update_rule(
        self, rule_id: uuid.UUID, data: ClosureRuleUpdate, actor_account_id: uuid.UUID
    ) -> ClosureRule:
        row = await self._rule(rule_id, lock=True)
        previous_state = row.review_state
        provided = data.model_fields_set
        content_fields = provided - {"review_state", "verified_at"}
        if row.review_state == "RETIRED" and (content_fields or data.review_state != "DRAFT"):
            raise conflict("rule_retired", "A retired rule only accepts review_state DRAFT")
        if row.review_state == "APPROVED" and content_fields:
            raise conflict(
                "rule_not_editable",
                "Approved rules are frozen; set review_state DRAFT first or retire it",
            )
        if data.rule_kind is not None:
            row.rule_kind = data.rule_kind
        if data.effect is not None:
            row.effect = data.effect
        if data.severity is not None:
            row.severity = data.severity
        if data.note_vi is not None:
            row.note_vi = data.note_vi
        if data.note_en is not None:
            row.note_en = data.note_en
        if "effective_from" in provided:
            row.effective_from = data.effective_from
        if "effective_to" in provided:
            row.effective_to = data.effective_to
        if "source_revision_id" in provided:
            if data.source_revision_id is not None:
                await require_source_revisions(self._session, [data.source_revision_id])
            row.source_revision_id = data.source_revision_id
        if data.params is not None or data.rule_kind is not None:
            row.params = validate_params(
                row.rule_kind, data.params if data.params is not None else row.params
            )
        _check_range(row.effective_from, row.effective_to)
        if data.review_state is not None and data.review_state != row.review_state:
            if data.review_state == "APPROVED":
                if row.source_revision_id is None:
                    raise invalid(
                        "rule_source_required", "An approved rule needs a source revision"
                    )
                row.verified_at = data.verified_at or datetime.now(UTC)
                row.reviewed_by_account_id = actor_account_id
            row.review_state = data.review_state
        await flush(self._session)
        self._audit(actor_account_id, row, "update", previous_state)
        await commit(self._session)
        await self._session.refresh(row)
        return to_schema(row)

    async def delete_rule(self, rule_id: uuid.UUID, actor_account_id: uuid.UUID) -> None:
        row = await self._rule(rule_id, lock=True)
        if row.review_state != "DRAFT":
            raise conflict(
                "rule_not_deletable", "Only DRAFT rules can be deleted; retire approved rules"
            )
        self._audit(actor_account_id, row, "delete", row.review_state)
        await self._session.delete(row)
        await commit(self._session)

    # ---- internals ----------------------------------------------------------------------

    async def _rule(self, rule_id: uuid.UUID, *, lock: bool = False) -> PlaceClosureRule:
        statement = select(PlaceClosureRule).where(PlaceClosureRule.id == rule_id)
        if lock:
            statement = statement.with_for_update()
        row = await self._session.scalar(statement)
        if row is None:
            raise not_found("Closure rule not found")
        return row

    async def _require_area(self, area_code: str | None, city_id: uuid.UUID) -> None:
        if area_code is None:
            raise invalid("invalid_rule_target", "AREA rules need an area_code")
        found = await self._session.scalar(
            select(Area.code).where(Area.code == area_code, Area.city_id == city_id)
        )
        if found is None:
            raise invalid("unknown_area", "Unknown area for this city", area_code=area_code)

    def _audit(
        self,
        actor_account_id: uuid.UUID,
        row: PlaceClosureRule,
        operation: str,
        from_state: str | None,
    ) -> None:
        audit(
            self._session,
            actor_account_id=actor_account_id,
            entity_table="place_closure_rules",
            entity_id=row.id,
            action="FACT_REVIEW",
            from_state=from_state,
            to_state=None if operation == "delete" else row.review_state,
            detail={
                "operation": operation,
                "rule_kind": row.rule_kind,
                "applies_to": row.applies_to,
                "place_id": str(row.place_id) if row.place_id else None,
                "area_code": row.area_code,
            },
        )


def _check_range(effective_from: date | None, effective_to: date | None) -> None:
    if effective_from is not None and effective_to is not None and effective_from > effective_to:
        raise invalid("invalid_effective_range", "effective_from must not be after effective_to")


def to_schema(row: PlaceClosureRule) -> ClosureRule:
    return ClosureRule.model_validate(row, from_attributes=True)

"""Calendar-rule parameter validation (DEC-016, ADR-011 0.3). AI never writes rules.

``params`` is validated per ``rule_kind`` by the Pydantic models below (the DB only checks
that it is an object), so Plan Health can trust approved rows. Every kind also accepts an
optional ``from``/``to`` window ("HH:MM") and ``restricted_modes`` (WALK, DRIVE, TWO_WHEELER).
Rules are loaded from the operator calendar (``app.ingestion.calendar``, DEC-022).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.errors import invalid

_HHMM = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"
_MMDD = r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"


RESTRICTED_MODES = ("WALK", "DRIVE", "TWO_WHEELER")


class _Params(BaseModel):
    """Keys every rule_kind accepts: a time window within the day and restricted travel modes."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    from_: str | None = Field(default=None, alias="from", pattern=_HHMM)
    to: str | None = Field(default=None, pattern=_HHMM)
    restricted_modes: list[Literal["WALK", "DRIVE", "TWO_WHEELER"]] | None = Field(
        default=None, min_length=1, max_length=3
    )

    @model_validator(mode="after")
    def _window(self) -> _Params:
        if (self.from_ is None) != (self.to is None):
            raise ValueError("from and to go together")
        if self.restricted_modes is not None and len(set(self.restricted_modes)) != len(
            self.restricted_modes
        ):
            raise ValueError("restricted_modes are unique")
        return self


class WeeklyParams(_Params):
    weekdays: list[int] = Field(min_length=1, max_length=7)

    @field_validator("weekdays")
    @classmethod
    def _iso_weekdays(cls, value: list[int]) -> list[int]:
        if any(day < 1 or day > 7 for day in value) or len(set(value)) != len(value):
            raise ValueError("weekdays are unique ISO days 1..7 (1 = Monday)")
        return value


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

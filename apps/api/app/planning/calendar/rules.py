"""Typed closure rules and their calendar occurrence (ADR-011 0.3, FR-102, DEC-016).

A :class:`ClosureRule` is built from a ``place_closure_rules`` row (any object with the column
attributes) or a mapping. ``params`` is parsed per ``rule_kind``; the shapes follow the column
comment in ``migrations/versions/20261106_0002_catalog.py``:

- ``WEEKLY`` ``{"weekdays": [1..7]}`` (ISO, 1 = Monday)
- ``DATE`` ``{"dates": ["YYYY-MM-DD"]}`` or ``{"month_day": ["MM-DD"]}`` (yearly)
- ``LUNAR_DATE`` ``{"lunar_days": [1, 14, 15], "lunar_months": [...] | null}``
- ``SEASON`` ``{"from_month_day": "MM-DD", "to_month_day": "MM-DD"}`` (may wrap over 31 Dec)
- ``TICKET_VALIDITY`` ``{"valid_same_day": true}`` or ``{"valid_hours": 24}``

Every kind additionally accepts two optional, effect-level keys that Plan Health uses:

- ``"from"`` / ``"to"`` (``HH:MM``, together): the time-of-day window the effect covers. ``CLOSED``
  removes it from the opening hours, ``PARTIAL`` keeps only it, ``EVENT``/``NOTICE`` warn only for
  visits overlapping it, a mode restriction holds only for legs departing inside it.
- ``"restricted_modes"`` (``["WALK" | "DRIVE" | "TWO_WHEELER"]``): travel modes not allowed between
  two stops that are both covered by this rule on that date (e.g. a car-free Old Town;
  LEG_MODE_RESTRICTED). ``TWO_WHEELER`` is accepted because the curator validator accepts it; the
  planner only schedules WALK and DRIVE legs, so it never matches a leg today.

The param models duplicate the curator validators in ``app/curation/closure_rules.py`` on
purpose: planning must stay importable without the curation services (SQLAlchemy sessions,
admin schemas). They are lenient about unknown keys so a curator-side addition never breaks
Plan Health; the curator API remains the strict gate.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from app.planning.calendar.lunar import solar_to_lunar

RuleKind = Literal["WEEKLY", "DATE", "LUNAR_DATE", "SEASON", "TICKET_VALIDITY"]
RuleEffect = Literal["CLOSED", "PARTIAL", "EVENT", "NOTICE"]
AppliesTo = Literal["PLACE", "AREA", "CITY"]
Severity = Literal["BLOCKING", "WARNING"]
ReviewState = Literal["DRAFT", "APPROVED", "RETIRED"]
TravelMode = Literal["WALK", "DRIVE"]
# Modes a rule may restrict: the curator set (app/curation/closure_rules.py RESTRICTED_MODES).
RestrictedMode = Literal["WALK", "DRIVE", "TWO_WHEELER"]

_HHMM = r"^(([01][0-9]|2[0-3]):[0-5][0-9]|24:00)$"
_MMDD = r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"

__all__ = [
    "AppliesTo",
    "ClosureRule",
    "DateParams",
    "LunarDateParams",
    "RestrictedMode",
    "ReviewState",
    "RuleEffect",
    "RuleKind",
    "RuleParams",
    "SeasonParams",
    "Severity",
    "TicketValidityParams",
    "TravelMode",
    "WeeklyParams",
    "describe_rule_error",
    "hhmm_to_minutes",
    "occurs_on",
]


def hhmm_to_minutes(value: str) -> int:
    """``"HH:MM"`` (``"24:00"`` allowed) → minutes after local midnight."""
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)


def describe_rule_error(exc: ValueError) -> str:
    """Why a rule did not parse, as ``loc: message`` pairs without the offending input values.

    Safe to log: Pydantic messages name the expected shape, never the rule text or params values
    (``include_input=False``; the ``params.`` prefix comes from :meth:`ClosureRule._parse_params`).
    """
    if isinstance(exc, ValidationError):
        parts = []
        for error in exc.errors(include_input=False, include_url=False, include_context=False):
            loc = ".".join(str(item) for item in error["loc"]) or "rule"
            parts.append(f"{loc}: {error['msg']}")
        return "; ".join(parts)[:500]
    return str(exc)[:500]


def _month_day(value: str) -> tuple[int, int]:
    month, day = value.split("-")
    return int(month), int(day)


class RuleParams(BaseModel):
    """Keys shared by every rule kind (see module docstring)."""

    model_config = ConfigDict(extra="ignore", frozen=True, populate_by_name=True)

    from_: str | None = Field(default=None, alias="from", pattern=_HHMM)
    to: str | None = Field(default=None, pattern=_HHMM)
    restricted_modes: tuple[RestrictedMode, ...] = ()

    @model_validator(mode="after")
    def _time_window(self) -> Self:
        if (self.from_ is None) != (self.to is None):
            raise ValueError("from and to go together")
        if self.from_ is not None and self.to is not None:
            if hhmm_to_minutes(self.from_) >= hhmm_to_minutes(self.to):
                raise ValueError("from must be before to")
        return self

    @property
    def interval(self) -> tuple[int, int] | None:
        """The ``from``/``to`` window in minutes, or ``None`` for the whole day."""
        if self.from_ is None or self.to is None:
            return None
        return hhmm_to_minutes(self.from_), hhmm_to_minutes(self.to)


class WeeklyParams(RuleParams):
    weekdays: tuple[int, ...] = Field(min_length=1, max_length=7)

    @field_validator("weekdays")
    @classmethod
    def _iso(cls, value: tuple[int, ...]) -> tuple[int, ...]:
        if any(day < 1 or day > 7 for day in value):
            raise ValueError("weekdays are ISO days 1..7 (1 = Monday)")
        return value


class DateParams(RuleParams):
    dates: tuple[date, ...] | None = None
    month_day: tuple[str, ...] | None = None

    @field_validator("month_day")
    @classmethod
    def _month_days(cls, value: tuple[str, ...] | None) -> tuple[str, ...] | None:
        if value is not None and not all(re.fullmatch(_MMDD, item) for item in value):
            raise ValueError("month_day items are MM-DD")
        return value

    @model_validator(mode="after")
    def _exactly_one(self) -> Self:
        if (self.dates is None) == (self.month_day is None):
            raise ValueError("give exactly one of dates or month_day")
        return self


class LunarDateParams(RuleParams):
    lunar_days: tuple[int, ...] = Field(min_length=1)
    lunar_months: tuple[int, ...] | None = None

    @model_validator(mode="after")
    def _ranges(self) -> Self:
        if any(day < 1 or day > 30 for day in self.lunar_days):
            raise ValueError("lunar_days are 1..30")
        if self.lunar_months is not None and any(m < 1 or m > 12 for m in self.lunar_months):
            raise ValueError("lunar_months are 1..12")
        return self


class SeasonParams(RuleParams):
    from_month_day: str = Field(pattern=_MMDD)
    to_month_day: str = Field(pattern=_MMDD)


class TicketValidityParams(RuleParams):
    valid_same_day: bool | None = None
    valid_hours: int | None = Field(default=None, ge=1, le=168)

    @model_validator(mode="after")
    def _exactly_one(self) -> Self:
        if (self.valid_same_day is None) == (self.valid_hours is None):
            raise ValueError("give exactly one of valid_same_day or valid_hours")
        return self


_PARAMS_BY_KIND: dict[str, type[RuleParams]] = {
    "WEEKLY": WeeklyParams,
    "DATE": DateParams,
    "LUNAR_DATE": LunarDateParams,
    "SEASON": SeasonParams,
    "TICKET_VALIDITY": TicketValidityParams,
}

_COLUMNS = (
    "id",
    "city_id",
    "applies_to",
    "place_id",
    "area_code",
    "rule_kind",
    "effect",
    "severity",
    "params",
    "effective_from",
    "effective_to",
    "review_state",
)


class ClosureRule(BaseModel):
    """One curator-reviewed calendar rule with parsed ``params``."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: uuid.UUID
    city_id: uuid.UUID | None = None
    applies_to: AppliesTo
    place_id: uuid.UUID | None = None
    area_code: str | None = None
    rule_kind: RuleKind
    effect: RuleEffect
    severity: Severity | None = None
    params: RuleParams
    effective_from: date | None = None
    effective_to: date | None = None
    review_state: ReviewState = "APPROVED"

    @model_validator(mode="before")
    @classmethod
    def _parse_params(cls, data: Any) -> Any:
        if isinstance(data, Mapping):
            values = dict(data)
            kind = values.get("rule_kind")
            raw = values.get("params")
            if kind in _PARAMS_BY_KIND and not isinstance(raw, RuleParams):
                try:
                    values["params"] = _PARAMS_BY_KIND[kind].model_validate(raw or {})
                except ValidationError as exc:
                    # Re-raise without the input values so the reason is safe to log.
                    raise ValueError(f"params.{describe_rule_error(exc)}") from None
            for key in ("effective_from", "effective_to"):
                if isinstance(values.get(key), datetime):
                    values[key] = values[key].date()
            return values
        return data

    @model_validator(mode="after")
    def _target(self) -> Self:
        if not isinstance(self.params, _PARAMS_BY_KIND[self.rule_kind]):
            raise ValueError(f"params do not match rule_kind {self.rule_kind}")
        if self.applies_to == "PLACE" and self.place_id is None:
            raise ValueError("PLACE rules need place_id")
        if self.applies_to == "AREA" and self.area_code is None:
            raise ValueError("AREA rules need area_code")
        if self.applies_to == "CITY" and self.city_id is None:
            raise ValueError("CITY rules need city_id")
        if (
            self.effective_from is not None
            and self.effective_to is not None
            and self.effective_from > self.effective_to
        ):
            raise ValueError("effective_from must not be after effective_to")
        return self

    @classmethod
    def from_row(cls, row: object) -> ClosureRule:
        """Build from a ``PlaceClosureRule`` ORM row (or any object with the same attributes)."""
        return cls.model_validate({name: getattr(row, name, None) for name in _COLUMNS})

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ClosureRule:
        return cls.model_validate(dict(data))

    @property
    def is_active(self) -> bool:
        """Only curator-approved rules are evaluated (FR-107)."""
        return self.review_state == "APPROVED"

    @property
    def interval(self) -> tuple[int, int] | None:
        return self.params.interval

    @property
    def restricted_modes(self) -> tuple[RestrictedMode, ...]:
        return self.params.restricted_modes


def _in_effect(rule: ClosureRule, day: date) -> bool:
    if rule.effective_from is not None and day < rule.effective_from:
        return False
    return rule.effective_to is None or day <= rule.effective_to


def occurs_on(rule: ClosureRule, day: date) -> bool:
    """Whether ``rule`` applies on the local calendar date ``day``.

    Pure calendar logic: honours ``effective_from``/``effective_to`` (inclusive) and the rule kind;
    it does not check ``review_state`` or the rule target (see :attr:`ClosureRule.is_active`).
    ``TICKET_VALIDITY`` occurs on every date in effect (it qualifies a ticket, not a date).
    For ``LUNAR_DATE`` with ``lunar_months`` set, only regular months match; a leap (nhuận)
    month matches only when ``lunar_months`` is null (every month).
    """
    if not _in_effect(rule, day):
        return False
    params = rule.params
    if isinstance(params, WeeklyParams):
        return day.isoweekday() in params.weekdays
    if isinstance(params, DateParams):
        if params.dates is not None:
            return day in params.dates
        return any(_month_day(item) == (day.month, day.day) for item in params.month_day or ())
    if isinstance(params, LunarDateParams):
        lunar = solar_to_lunar(day)
        if lunar.day not in params.lunar_days:
            return False
        if params.lunar_months is None:
            return True
        return not lunar.leap and lunar.month in params.lunar_months
    if isinstance(params, SeasonParams):
        start = _month_day(params.from_month_day)
        end = _month_day(params.to_month_day)
        current = (day.month, day.day)
        if start <= end:
            return start <= current <= end
        return current >= start or current <= end
    return isinstance(params, TicketValidityParams)

"""Plan Health: deterministic feasibility check of a plan (ADR-011 0.3, architecture §3.2 step 7).

Pure code, no I/O and no model output (NFR-032). Input is a minimal typed plan
(:class:`HealthPlan`) plus the effective windows from :mod:`app.planning.calendar.windows`;
output is the contract ``PlanHealth`` status and ``Conflict`` list (openapi ``Conflict``).

Severity is fixed per conflict type (architecture §3.6, openapi ``Conflict.type``):

- BLOCKING: ``CLOSED_AT_PLANNED_TIME``, ``CLOSED_ON_DATE``, ``LEG_UNAVAILABLE``,
  ``LEG_MODE_RESTRICTED``, ``DAY_WINDOW_EXCEEDED``, ``WEB_PLACE_UNRESOLVED``.
- WARNING: ``FACT_STALE``, ``MUST_SEE_NOT_INCLUDED``, ``LUNAR_EVENT_CONFLICT``,
  ``TICKET_VALIDITY``, ``SEASONAL_WARNING``, ``WEB_PLACE_UNVERIFIED``.
- INFO: ``OPENING_HOURS_UNKNOWN`` (missing data, not a plan problem; DEC-030 amends ADR-011) and
  ``LEG_ESTIMATED`` (a leg measured by the demo estimate provider, not Google Routes).

``plan_health`` is ``BLOCKED`` iff a blocking conflict exists, else ``WARNING`` if any warning
exists or any stop is ``WEB_UNVERIFIED`` (FR-031 cap), else ``GOOD``. INFO notices never change
the status: unknown hours stay unknown and an estimated leg is labelled on the leg; neither makes
a feasible plan worse.

Messages: each conflict has a stable ``message_key`` for the mobile i18n catalogue and a fixed
English ``message`` as fallback; neither contains user or place text.
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.planning.calendar.rules import TravelMode
from app.planning.calendar.windows import DAY_MINUTES, DayWindow, Interval, contains, overlaps

ConflictType = Literal[
    "CLOSED_AT_PLANNED_TIME",
    "LEG_UNAVAILABLE",
    "DAY_WINDOW_EXCEEDED",
    "OPENING_HOURS_UNKNOWN",
    "FACT_STALE",
    "MUST_SEE_NOT_INCLUDED",
    "CLOSED_ON_DATE",
    "LEG_MODE_RESTRICTED",
    "LUNAR_EVENT_CONFLICT",
    "TICKET_VALIDITY",
    "SEASONAL_WARNING",
    "WEB_PLACE_UNVERIFIED",
    "WEB_PLACE_UNRESOLVED",
    "LEG_ESTIMATED",
]
Severity = Literal["BLOCKING", "WARNING", "INFO"]
PlanHealthStatus = Literal["GOOD", "WARNING", "BLOCKED"]
TrustLevel = Literal["VERIFIED", "WEB_UNVERIFIED"]
LegAvailability = Literal["AVAILABLE", "UNAVAILABLE", "EXPIRED"]

DEFAULT_STALE_AFTER_DAYS = 180
"""FR-005 / ASM-008: a fact is stale when verified more than 180 days before today."""

CONFLICT_SEVERITY: Mapping[ConflictType, Severity] = {
    "CLOSED_AT_PLANNED_TIME": "BLOCKING",
    "LEG_UNAVAILABLE": "BLOCKING",
    "DAY_WINDOW_EXCEEDED": "BLOCKING",
    "OPENING_HOURS_UNKNOWN": "INFO",  # DEC-030: missing data, not a plan problem
    "FACT_STALE": "WARNING",
    "MUST_SEE_NOT_INCLUDED": "WARNING",
    "CLOSED_ON_DATE": "BLOCKING",
    "LEG_MODE_RESTRICTED": "BLOCKING",
    "LUNAR_EVENT_CONFLICT": "WARNING",
    "TICKET_VALIDITY": "WARNING",
    "SEASONAL_WARNING": "WARNING",
    "WEB_PLACE_UNVERIFIED": "WARNING",
    "WEB_PLACE_UNRESOLVED": "BLOCKING",
    "LEG_ESTIMATED": "INFO",
}

CONFLICT_MESSAGES: Mapping[ConflictType, str] = {
    "CLOSED_AT_PLANNED_TIME": "The place is closed at the planned time.",
    "LEG_UNAVAILABLE": "No route is available for this leg.",
    "DAY_WINDOW_EXCEEDED": "The day runs outside its start or end time.",
    "OPENING_HOURS_UNKNOWN": "Opening hours are unknown; check before you go.",
    "FACT_STALE": "Some details were last verified more than 180 days ago.",
    "MUST_SEE_NOT_INCLUDED": "A must-see place is not in the plan.",
    "CLOSED_ON_DATE": "The place is closed on this date.",
    "LEG_MODE_RESTRICTED": "This travel mode is not allowed for this leg on this date.",
    "LUNAR_EVENT_CONFLICT": "A lunar-calendar event affects this visit.",
    "TICKET_VALIDITY": "The ticket for this area is not valid for every planned visit.",
    "SEASONAL_WARNING": "A seasonal or dated notice applies to this visit.",
    "WEB_PLACE_UNVERIFIED": "This place was found on the web and is not verified by Gonarra.",
    "WEB_PLACE_UNRESOLVED": "This web-found place could not be confirmed to exist.",
    "LEG_ESTIMATED": "Travel time and distance are estimates, not measured routes.",
}

_TYPE_ORDER: Mapping[str, int] = {name: index for index, name in enumerate(CONFLICT_SEVERITY)}

__all__ = [
    "CONFLICT_MESSAGES",
    "CONFLICT_SEVERITY",
    "DEFAULT_STALE_AFTER_DAYS",
    "ConflictType",
    "HealthConflict",
    "HealthDay",
    "HealthLeg",
    "HealthPlan",
    "HealthResult",
    "HealthStop",
    "LegAvailability",
    "PlanHealthStatus",
    "Severity",
    "TrustLevel",
    "evaluate",
    "message_key",
]


def message_key(conflict_type: ConflictType) -> str:
    """Stable i18n key, e.g. ``plan_health.conflict.closed_on_date``."""
    return f"plan_health.conflict.{conflict_type.lower()}"


# ---- input ----------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class HealthStop:
    """One scheduled stop. Times are minutes after local midnight of the day's date.

    ``place_id`` is the catalog place, or the key under which the orchestrator supplied a window
    for a web candidate; ``None`` means no window (hours unknown). ``web_resolved`` is false for a
    web candidate whose Places check failed. ``fact_verified_at`` is the oldest verification date
    of the stop's displayed operational facts (``None`` = nothing to age).
    """

    stop_id: uuid.UUID
    place_id: uuid.UUID | None
    arrival_min: int
    departure_min: int
    trust_level: TrustLevel = "VERIFIED"
    must_see: bool = False
    web_resolved: bool = True
    fact_verified_at: date | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.arrival_min <= self.departure_min <= DAY_MINUTES:
            raise ValueError("stop times must satisfy 0 <= arrival <= departure <= 1440")

    @property
    def span(self) -> Interval:
        return self.arrival_min, self.departure_min


@dataclass(frozen=True, slots=True)
class HealthLeg:
    from_stop_id: uuid.UUID
    to_stop_id: uuid.UUID
    travel_mode: TravelMode
    availability: LegAvailability
    duration_s: int | None = None
    estimated: bool = False  # distance/duration from the demo estimate provider


@dataclass(frozen=True, slots=True)
class HealthDay:
    """One plan day; ``stops`` in visiting order; legs reference stops of this day only."""

    date: date
    start_min: int
    end_min: int
    stops: tuple[HealthStop, ...] = ()
    legs: tuple[HealthLeg, ...] = ()

    def __post_init__(self) -> None:
        if not 0 <= self.start_min < self.end_min <= DAY_MINUTES:
            raise ValueError("day window must satisfy 0 <= start < end <= 1440")
        ids = {stop.stop_id for stop in self.stops}
        if len(ids) != len(self.stops):
            raise ValueError("stop ids must be unique within a day")
        for leg in self.legs:
            if leg.from_stop_id not in ids or leg.to_stop_id not in ids:
                raise ValueError("legs must reference stops of the same day")


@dataclass(frozen=True, slots=True)
class HealthPlan:
    days: tuple[HealthDay, ...]
    must_see_place_ids: tuple[uuid.UUID, ...] = ()


# ---- output ---------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class HealthConflict:
    """Maps 1:1 onto the openapi ``Conflict`` (``message_key`` and ``place_id`` are extras:
    ``place_id`` names the missing place of ``MUST_SEE_NOT_INCLUDED``)."""

    type: ConflictType
    severity: Severity
    message_key: str
    message: str
    rule_id: uuid.UUID | None = None
    date: date | None = None
    stop_ids: tuple[uuid.UUID, ...] = ()
    place_id: uuid.UUID | None = None

    @property
    def blocking(self) -> bool:
        return self.severity == "BLOCKING"


@dataclass(frozen=True, slots=True)
class HealthResult:
    plan_health: PlanHealthStatus
    conflicts: tuple[HealthConflict, ...]

    @property
    def blocking(self) -> tuple[HealthConflict, ...]:
        return tuple(c for c in self.conflicts if c.blocking)


def _conflict(
    kind: ConflictType,
    *,
    day: date | None = None,
    stop_ids: tuple[uuid.UUID, ...] = (),
    rule_id: uuid.UUID | None = None,
    place_id: uuid.UUID | None = None,
) -> HealthConflict:
    return HealthConflict(
        type=kind,
        severity=CONFLICT_SEVERITY[kind],
        message_key=message_key(kind),
        message=CONFLICT_MESSAGES[kind],
        rule_id=rule_id,
        date=day,
        stop_ids=stop_ids,
        place_id=place_id,
    )


# ---- checks ---------------------------------------------------------------------------------


def _check_window(stop: HealthStop, day: date, window: DayWindow | None) -> list[HealthConflict]:
    found: list[HealthConflict] = []
    ids = (stop.stop_id,)
    if window is None:
        return [_conflict("OPENING_HOURS_UNKNOWN", day=day, stop_ids=ids)]
    if window.closed_rule_ids:
        found.extend(
            _conflict("CLOSED_ON_DATE", day=day, stop_ids=ids, rule_id=rule_id)
            for rule_id in window.closed_rule_ids
        )
    elif not window.unknown_hours and not window.base_intervals:
        # Regular hours list nothing for this weekday: closed on this date, no rule behind it.
        found.append(_conflict("CLOSED_ON_DATE", day=day, stop_ids=ids))
    else:
        found.extend(_check_planned_time(stop, day, window))
    if window.unknown_hours:
        found.append(_conflict("OPENING_HOURS_UNKNOWN", day=day, stop_ids=ids))
    for notice in window.notices:
        if notice.conflict_type == "TICKET_VALIDITY":
            continue  # evaluated across the whole plan
        if notice.interval is None or overlaps(notice.interval, stop.span):
            found.append(
                _conflict(notice.conflict_type, day=day, stop_ids=ids, rule_id=notice.rule_id)
            )
    return found


def _check_planned_time(stop: HealthStop, day: date, window: DayWindow) -> list[HealthConflict]:
    """CLOSED_AT_PLANNED_TIME, attributed to the narrowing rule when one caused it.

    With unknown hours the default window is scheduling-only, so only rule adjustments can make
    a visit "closed"; the stop is never called closed merely for leaving the default window.
    """
    ids = (stop.stop_id,)
    culprit = next(
        (
            adjustment.rule_id
            for adjustment in window.adjustments
            if (
                overlaps(adjustment.interval, stop.span)
                if adjustment.effect == "CLOSED"
                else not contains((adjustment.interval,), stop.span)
            )
        ),
        None,
    )
    if window.unknown_hours:
        if culprit is None:
            return []
        return [_conflict("CLOSED_AT_PLANNED_TIME", day=day, stop_ids=ids, rule_id=culprit)]
    if contains(window.intervals, stop.span):
        return []
    if not contains(window.base_intervals, stop.span):
        culprit = None  # outside the regular hours whatever the rules say
    return [_conflict("CLOSED_AT_PLANNED_TIME", day=day, stop_ids=ids, rule_id=culprit)]


def _check_stop(
    stop: HealthStop,
    day: date,
    window: DayWindow | None,
    *,
    today: date,
    stale_after_days: int,
) -> list[HealthConflict]:
    ids = (stop.stop_id,)
    found: list[HealthConflict] = []
    if stop.trust_level == "WEB_UNVERIFIED":
        kind: ConflictType = "WEB_PLACE_UNVERIFIED" if stop.web_resolved else "WEB_PLACE_UNRESOLVED"
        found.append(_conflict(kind, day=day, stop_ids=ids))
    found.extend(_check_window(stop, day, window))
    if (
        stop.fact_verified_at is not None
        and (today - stop.fact_verified_at).days > stale_after_days
    ):
        found.append(_conflict("FACT_STALE", day=day, stop_ids=ids))
    return found


def _check_day(
    day: HealthDay, windows: Mapping[tuple[uuid.UUID, date], DayWindow]
) -> list[HealthConflict]:
    found: list[HealthConflict] = []
    outside = tuple(
        stop.stop_id
        for stop in day.stops
        if stop.arrival_min < day.start_min or stop.departure_min > day.end_min
    )
    if outside:
        found.append(_conflict("DAY_WINDOW_EXCEEDED", day=day.date, stop_ids=outside))
    stops = {stop.stop_id: stop for stop in day.stops}
    for leg in day.legs:
        pair = (leg.from_stop_id, leg.to_stop_id)
        if leg.availability != "AVAILABLE":
            found.append(_conflict("LEG_UNAVAILABLE", day=day.date, stop_ids=pair))
        elif leg.estimated:
            found.append(_conflict("LEG_ESTIMATED", day=day.date, stop_ids=pair))
        origin, target = stops[leg.from_stop_id], stops[leg.to_stop_id]
        found.extend(
            _conflict("LEG_MODE_RESTRICTED", day=day.date, stop_ids=pair, rule_id=rule_id)
            for rule_id in _restricting_rules(leg, origin, target, day.date, windows)
        )
    return found


def _restricting_rules(
    leg: HealthLeg,
    origin: HealthStop,
    target: HealthStop,
    day: date,
    windows: Mapping[tuple[uuid.UUID, date], DayWindow],
) -> list[uuid.UUID]:
    """Rules restricting ``leg.travel_mode`` that cover both ends of the leg on ``day``."""
    if origin.place_id is None or target.place_id is None:
        return []
    start = windows.get((origin.place_id, day))
    end = windows.get((target.place_id, day))
    if start is None or end is None:
        return []
    end_rules = {restriction.rule_id for restriction in end.mode_restrictions}
    departure = origin.departure_min
    rule_ids: list[uuid.UUID] = []
    for restriction in start.mode_restrictions:
        if leg.travel_mode not in restriction.modes or restriction.rule_id not in end_rules:
            continue
        span = restriction.interval
        if span is not None and not span[0] <= departure < span[1]:
            continue
        rule_ids.append(restriction.rule_id)
    return rule_ids


def _check_tickets(
    plan: HealthPlan, windows: Mapping[tuple[uuid.UUID, date], DayWindow]
) -> list[HealthConflict]:
    """TICKET_VALIDITY across days: a same-day ticket used on several dates, or visits spanning
    longer than ``valid_hours`` from the first arrival."""
    visits: dict[uuid.UUID, list[tuple[int, int, date, uuid.UUID]]] = defaultdict(list)
    rules: dict[uuid.UUID, tuple[bool | None, int | None]] = {}
    for day in plan.days:
        for stop in day.stops:
            window = windows.get((stop.place_id, day.date)) if stop.place_id else None
            if window is None:
                continue
            for notice in window.notices:
                if notice.conflict_type != "TICKET_VALIDITY":
                    continue
                if notice.interval is not None and not overlaps(notice.interval, stop.span):
                    continue
                base = day.date.toordinal() * DAY_MINUTES
                visits[notice.rule_id].append(
                    (base + stop.arrival_min, base + stop.departure_min, day.date, stop.stop_id)
                )
                rules[notice.rule_id] = (notice.ticket_valid_same_day, notice.ticket_valid_hours)
    found: list[HealthConflict] = []
    for rule_id, entries in visits.items():
        entries.sort()
        same_day, valid_hours = rules[rule_id]
        if same_day:
            first_date = entries[0][2]
            for later in sorted({entry[2] for entry in entries} - {first_date}):
                ids = tuple(entry[3] for entry in entries if entry[2] == later)
                found.append(_conflict("TICKET_VALIDITY", day=later, stop_ids=ids, rule_id=rule_id))
        elif valid_hours is not None:
            expires = entries[0][0] + valid_hours * 60
            late = [entry for entry in entries if entry[1] > expires]
            if late:
                found.append(
                    _conflict(
                        "TICKET_VALIDITY",
                        day=late[0][2],
                        stop_ids=tuple(entry[3] for entry in late),
                        rule_id=rule_id,
                    )
                )
    return found


def _sort_key(conflict: HealthConflict) -> tuple[bool, date, int, tuple[str, ...], str, str]:
    return (
        conflict.date is None,
        conflict.date or date.min,
        _TYPE_ORDER[conflict.type],
        tuple(str(stop_id) for stop_id in conflict.stop_ids),
        str(conflict.rule_id or ""),
        str(conflict.place_id or ""),
    )


def evaluate(
    plan: HealthPlan,
    windows: Mapping[tuple[uuid.UUID, date], DayWindow],
    *,
    today: date,
    stale_after_days: int = DEFAULT_STALE_AFTER_DAYS,
) -> HealthResult:
    """Evaluate ``plan`` against the effective ``windows`` (from ``effective_windows``).

    Conflicts are de-duplicated and ordered by date (date-less last), contract type order, stop
    ids, rule id and place id, so identical inputs give identical output (NFR-032).
    """
    found: list[HealthConflict] = []
    for day in plan.days:
        for stop in day.stops:
            window = windows.get((stop.place_id, day.date)) if stop.place_id else None
            found.extend(
                _check_stop(stop, day.date, window, today=today, stale_after_days=stale_after_days)
            )
        found.extend(_check_day(day, windows))
    found.extend(_check_tickets(plan, windows))
    planned = {stop.place_id for day in plan.days for stop in day.stops}
    found.extend(
        _conflict("MUST_SEE_NOT_INCLUDED", place_id=place_id)
        for place_id in dict.fromkeys(plan.must_see_place_ids)
        if place_id not in planned
    )
    conflicts = tuple(sorted(dict.fromkeys(found), key=_sort_key))
    has_web = any(stop.trust_level == "WEB_UNVERIFIED" for day in plan.days for stop in day.stops)
    status: PlanHealthStatus
    if any(conflict.blocking for conflict in conflicts):
        status = "BLOCKED"
    elif has_web or any(conflict.severity == "WARNING" for conflict in conflicts):
        status = "WARNING"
    else:
        status = "GOOD"
    return HealthResult(plan_health=status, conflicts=conflicts)

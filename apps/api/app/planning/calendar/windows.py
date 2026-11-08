"""Per-(place, date) effective windows from opening hours and closure rules (ADR-011 0.3, §3.6).

The solver schedules inside :attr:`DayWindow.intervals`; Plan Health reads the same windows to
explain conflicts. Times are minutes after local midnight (Asia/Ho_Chi_Minh); an interval is a
half-open ``(start, end)`` pair with ``0 <= start < end <= 1440``.

Unknown opening hours are never invented (BR on unknown facts, FR-005): the window is flagged
``unknown_hours`` and carries a configurable *scheduling-only* default interval so the solver can
still place the stop; Plan Health then emits an INFO ``OPENING_HOURS_UNKNOWN`` (DEC-030) and never
claims the place is closed outside that default.

Rule effects on a date the rule occurs (only ``APPROVED`` rules whose target covers the place):

- ``CLOSED`` without ``from``/``to`` → the day is closed (``closed_rule_ids``); with them → that
  time range is removed.
- ``PARTIAL`` with ``from``/``to`` → hours are narrowed to that range; without → a warning.
- ``EVENT``/``NOTICE`` → a warning (:class:`CalendarNotice`).
- ``TICKET_VALIDITY`` rules are notices whatever their effect (they qualify a ticket, not a date).
- ``restricted_modes`` on any rule → a :class:`ModeRestriction` for that date. Such a rule
  qualifies legs, not hours: it never closes the place and never narrows its opening window
  (a car-free Old Town is open all day; DEC-030-adjacent bug fixed 2026-11-09).
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

from app.planning.calendar.rules import (
    ClosureRule,
    RestrictedMode,
    RuleEffect,
    RuleKind,
    TicketValidityParams,
    hhmm_to_minutes,
    occurs_on,
)

Interval = tuple[int, int]
NoticeType = Literal["LUNAR_EVENT_CONFLICT", "SEASONAL_WARNING", "TICKET_VALIDITY"]

DAY_MINUTES = 24 * 60
SUPPORTED_TZ = "Asia/Ho_Chi_Minh"
DEFAULT_UNKNOWN_HOURS_WINDOW: Interval = (8 * 60, 18 * 60)
"""Scheduling-only window for a place whose opening hours are unknown (never shown as hours)."""

_WEEKDAY_KEYS = {"mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6, "sun": 7}

__all__ = [
    "DAY_MINUTES",
    "DEFAULT_UNKNOWN_HOURS_WINDOW",
    "CalendarNotice",
    "DayWindow",
    "Interval",
    "ModeRestriction",
    "NoticeType",
    "OpeningHours",
    "PlaceRef",
    "WindowAdjustment",
    "contains",
    "effective_windows",
    "overlaps",
    "rule_targets",
]


# ---- interval helpers -----------------------------------------------------------------------


def _normalise(intervals: Iterable[Interval]) -> tuple[Interval, ...]:
    """Sort, drop empty and merge overlapping or touching intervals."""
    merged: list[Interval] = []
    for start, end in sorted(i for i in intervals if i[0] < i[1]):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return tuple(merged)


def _intersect(intervals: Sequence[Interval], window: Interval) -> tuple[Interval, ...]:
    return _normalise((max(s, window[0]), min(e, window[1])) for s, e in intervals)


def _subtract(intervals: Sequence[Interval], hole: Interval) -> tuple[Interval, ...]:
    pieces: list[Interval] = []
    for start, end in intervals:
        pieces.append((start, min(end, hole[0])))
        pieces.append((max(start, hole[1]), end))
    return _normalise(pieces)


def overlaps(a: Interval, b: Interval) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def contains(intervals: Sequence[Interval], span: Interval) -> bool:
    """Whether one interval covers ``span`` entirely (a zero-length span needs ``start < end``)."""
    return any(s <= span[0] and span[1] <= e for s, e in intervals)


# ---- inputs ---------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class OpeningHours:
    """Regular weekly opening hours: ISO weekday (1 = Monday) → open intervals in minutes.

    A weekday missing from ``by_weekday`` (or mapped to no interval) means closed that weekday.
    """

    by_weekday: Mapping[int, tuple[Interval, ...]]

    @classmethod
    def from_value(cls, value: Mapping[str, Any]) -> OpeningHours:
        """Parse an ``OPENING_HOURS`` fact value.

        Accepted shape: weekday key (``"1"``..``"7"`` or ``"mon"``..``"sun"``) → list of
        ``["HH:MM", "HH:MM"]`` pairs; optionally nested under ``"weekly"``. A closing time at or
        before the opening time (past midnight) is clamped to ``24:00`` — a plan day never runs
        past midnight (``day_overflow``).
        """
        raw = value.get("weekly", value)
        by_weekday: dict[int, tuple[Interval, ...]] = {}
        for key, pairs in raw.items():
            weekday = _WEEKDAY_KEYS.get(str(key).lower()) or int(key)
            if not 1 <= weekday <= 7:
                raise ValueError(f"weekday {key!r} is not 1..7")
            spans: list[Interval] = []
            for opens, closes in pairs:
                start, end = hhmm_to_minutes(opens), hhmm_to_minutes(closes)
                spans.append((start, end if end > start else DAY_MINUTES))
            by_weekday[weekday] = _normalise(spans)
        return cls(by_weekday=by_weekday)

    @classmethod
    def every_day(cls, opens: str, closes: str) -> OpeningHours:
        span = (hhmm_to_minutes(opens), hhmm_to_minutes(closes))
        return cls(by_weekday={weekday: (span,) for weekday in range(1, 8)})

    def on(self, day: date) -> tuple[Interval, ...]:
        return _normalise(self.by_weekday.get(day.isoweekday(), ()))


@dataclass(frozen=True, slots=True)
class PlaceRef:
    """What rule targeting needs to know about a place (or a web candidate)."""

    place_id: uuid.UUID
    area_code: str | None = None
    city_id: uuid.UUID | None = None


# ---- outputs --------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class WindowAdjustment:
    """A rule that removed (``CLOSED``) or narrowed to (``PARTIAL``) a time range."""

    rule_id: uuid.UUID
    effect: RuleEffect
    interval: Interval


@dataclass(frozen=True, slots=True)
class CalendarNotice:
    """A non-blocking calendar rule that holds on this date (EVENT, NOTICE, SEASON, ticket)."""

    rule_id: uuid.UUID
    rule_kind: RuleKind
    effect: RuleEffect
    conflict_type: NoticeType
    interval: Interval | None = None
    ticket_valid_same_day: bool | None = None
    ticket_valid_hours: int | None = None


@dataclass(frozen=True, slots=True)
class ModeRestriction:
    """Travel modes not allowed between two stops both covered by ``rule_id`` on this date."""

    rule_id: uuid.UUID
    modes: frozenset[RestrictedMode]
    interval: Interval | None = None


@dataclass(frozen=True, slots=True)
class DayWindow:
    """Effective opening of one place on one date.

    ``intervals`` is what the solver may use (empty = closed). When ``unknown_hours`` is true the
    intervals derive from the scheduling-only default, not from a fact.
    """

    place_id: uuid.UUID
    date: date
    intervals: tuple[Interval, ...]
    unknown_hours: bool
    base_intervals: tuple[Interval, ...] = ()
    closed_rule_ids: tuple[uuid.UUID, ...] = ()
    adjustments: tuple[WindowAdjustment, ...] = ()
    notices: tuple[CalendarNotice, ...] = ()
    mode_restrictions: tuple[ModeRestriction, ...] = field(default=())

    @property
    def is_closed(self) -> bool:
        return not self.intervals


def rule_targets(rule: ClosureRule, place: PlaceRef) -> bool:
    """Whether ``rule`` covers ``place`` (PLACE by id, AREA by area code, CITY by city)."""
    if rule.applies_to == "PLACE":
        return rule.place_id == place.place_id
    if rule.city_id is not None and place.city_id is not None and rule.city_id != place.city_id:
        return False
    if rule.applies_to == "AREA":
        return place.area_code is not None and rule.area_code == place.area_code
    return place.city_id is not None and rule.city_id == place.city_id


def _notice_type(rule: ClosureRule) -> NoticeType:
    if rule.rule_kind == "TICKET_VALIDITY":
        return "TICKET_VALIDITY"
    if rule.rule_kind == "LUNAR_DATE":
        return "LUNAR_EVENT_CONFLICT"
    return "SEASONAL_WARNING"


def _window_for(
    place: PlaceRef,
    day: date,
    hours: OpeningHours | None,
    rules: Sequence[ClosureRule],
    unknown_window: Interval,
) -> DayWindow:
    unknown = hours is None
    base = _normalise([unknown_window]) if hours is None else hours.on(day)
    intervals = base
    closed: list[uuid.UUID] = []
    adjustments: list[WindowAdjustment] = []
    notices: list[CalendarNotice] = []
    restrictions: list[ModeRestriction] = []
    for rule in rules:
        if not rule_targets(rule, place) or not occurs_on(rule, day):
            continue
        span = rule.interval
        mode_only = bool(rule.restricted_modes)
        if mode_only:
            # A mode restriction is about travel between stops, not about opening hours: the
            # Hội An Old Town is car-free 15:00–22:00 but its places stay open all day. Applying
            # the rule's PARTIAL window here once made every Old Town visit start at 15:00.
            restrictions.append(ModeRestriction(rule.id, frozenset(rule.restricted_modes), span))
        if not mode_only and rule.rule_kind != "TICKET_VALIDITY" and rule.effect == "CLOSED":
            if span is None:
                closed.append(rule.id)
            else:
                intervals = _subtract(intervals, span)
                adjustments.append(WindowAdjustment(rule.id, rule.effect, span))
            continue
        if (
            not mode_only
            and rule.rule_kind != "TICKET_VALIDITY"
            and rule.effect == "PARTIAL"
            and span
        ):
            intervals = _intersect(intervals, span)
            adjustments.append(WindowAdjustment(rule.id, rule.effect, span))
            continue
        params = rule.params
        ticket = params if isinstance(params, TicketValidityParams) else None
        notices.append(
            CalendarNotice(
                rule_id=rule.id,
                rule_kind=rule.rule_kind,
                effect=rule.effect,
                conflict_type=_notice_type(rule),
                interval=span,
                ticket_valid_same_day=ticket.valid_same_day if ticket else None,
                ticket_valid_hours=ticket.valid_hours if ticket else None,
            )
        )
    if closed:
        intervals = ()
    return DayWindow(
        place_id=place.place_id,
        date=day,
        intervals=intervals,
        unknown_hours=unknown,
        base_intervals=base,
        closed_rule_ids=tuple(closed),
        adjustments=tuple(adjustments),
        notices=tuple(notices),
        mode_restrictions=tuple(restrictions),
    )


def effective_windows(
    *,
    base_hours: Mapping[uuid.UUID, OpeningHours | None],
    rules: Sequence[ClosureRule],
    places: Sequence[PlaceRef],
    dates: Sequence[date],
    tz: str = SUPPORTED_TZ,
    unknown_hours_window: Interval = DEFAULT_UNKNOWN_HOURS_WINDOW,
) -> dict[tuple[uuid.UUID, date], DayWindow]:
    """Expand ``rules`` over ``places`` × ``dates`` into effective day windows.

    ``base_hours`` maps a place to its opening hours, or ``None``/absent when unknown. Rules that
    are not ``APPROVED`` are ignored. Output is deterministic: rules are applied in id order and
    the dict is keyed (and ordered) by ``places`` then ``dates``.
    """
    if tz != SUPPORTED_TZ:
        raise ValueError(f"only {SUPPORTED_TZ} is supported (Vietnamese lunar calendar, UTC+7)")
    start, end = unknown_hours_window
    if not 0 <= start < end <= DAY_MINUTES:
        raise ValueError("unknown_hours_window must satisfy 0 <= start < end <= 1440")
    active = sorted((rule for rule in rules if rule.is_active), key=lambda rule: str(rule.id))
    return {
        (place.place_id, day): _window_for(
            place, day, base_hours.get(place.place_id), active, unknown_hours_window
        )
        for place in places
        for day in dates
    }

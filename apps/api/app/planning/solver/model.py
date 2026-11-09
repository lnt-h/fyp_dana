"""Solver input/output types (ADR-011). Pure data: no DB, no routing provider, no AI.

Times are seconds since local midnight of the day's date (Asia/Ho_Chi_Minh, no DST). Effective
windows per (stop, date) come from the calendar module (closures, lunar dates, opening hours ∩
day window); the solver only enforces them.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date, time
from enum import StrEnum

SECONDS_PER_DAY = 86_400

# (origin_key, destination_key) -> seconds, or None when the leg is unavailable (forbidden arc).
DurationLookup = Callable[[str, str], int | None]


def seconds_of(value: time) -> int:
    return value.hour * 3600 + value.minute * 60 + value.second


def time_of(seconds: int) -> time:
    seconds = max(0, min(seconds, SECONDS_PER_DAY - 1))
    return time(seconds // 3600, (seconds % 3600) // 60, seconds % 60)


@dataclass(frozen=True, slots=True)
class Interval:
    """Closed interval ``[start_s, end_s]`` in seconds since local midnight; the visit must
    start and finish inside it."""

    start_s: int
    end_s: int

    def __post_init__(self) -> None:
        if not (0 <= self.start_s <= self.end_s <= SECONDS_PER_DAY):
            raise ValueError("interval must satisfy 0 <= start <= end <= 86400")

    @classmethod
    def of(cls, start: time, end: time) -> Interval:
        return cls(seconds_of(start), seconds_of(end))


@dataclass(frozen=True, slots=True)
class BreakSpec:
    """Optional lunch break of ``duration_s`` starting in ``[earliest_start_s, latest_start_s]``."""

    earliest_start_s: int
    latest_start_s: int
    duration_s: int

    def __post_init__(self) -> None:
        if self.duration_s <= 0 or self.earliest_start_s > self.latest_start_s:
            raise ValueError("invalid break")


@dataclass(frozen=True, slots=True)
class DaySpec:
    date: date
    start_s: int
    end_s: int
    start_key: str
    end_key: str
    lunch: BreakSpec | None = None
    # Pace: at most this many stops on the day (``None`` = no cap). Hard constraint.
    max_stops: int | None = None

    def __post_init__(self) -> None:
        if not (0 <= self.start_s < self.end_s <= SECONDS_PER_DAY):
            raise ValueError("day window must satisfy 0 <= start < end <= 86400")
        if self.max_stops is not None and self.max_stops < 0:
            raise ValueError("max_stops must be >= 0")


@dataclass(frozen=True, slots=True)
class Lock:
    """Stop pinned to ``day_index``; ``position`` orders locked stops within that day
    (unlocked stops may be inserted between them)."""

    day_index: int
    position: int


@dataclass(frozen=True, slots=True)
class StopSpec:
    key: str
    visit_minutes: int
    # Effective open intervals per date. A date that is missing, or maps to (), is CLOSED.
    windows: Mapping[date, tuple[Interval, ...]]
    rank: int = 0  # selector rank; 0 = best
    must_see: bool = False
    lock: Lock | None = None
    category: str | None = None  # for the per-category variety cap
    # Travel area of the place (PoolPlace.area_code): days serving many distinct areas pay
    # ``SolverParams.area_spread_penalty``, so far-apart places land on different days (Đợt 3).
    area: str | None = None
    # Places sharing a ticket that is valid only on its day of purchase (e.g. the Hội An Old
    # Town ticket). The solver prefers to serve one group on a single day (TICKET_VALIDITY).
    ticket_group: str | None = None

    def __post_init__(self) -> None:
        if self.visit_minutes <= 0:
            raise ValueError("visit_minutes must be > 0")
        if self.rank < 0:
            raise ValueError("rank must be >= 0")

    @property
    def visit_s(self) -> int:
        return self.visit_minutes * 60


@dataclass(frozen=True, slots=True)
class SolverParams:
    time_limit_s: float = 2.0
    # Deterministic work bound: the search stops after this many solutions, so the result does
    # not depend on machine speed. The time limit is only a safety cap (``time_limit_reached``).
    solution_limit: int = 400
    drop_penalty_base: int = 7_200  # ≈ seconds of extra travel worth one top-ranked stop
    drop_penalty_rank_step: int = 240
    drop_penalty_floor: int = 1_200
    must_see_penalty: int = 10_000_000
    lock_penalty: int = 100_000_000
    # Day balance: cost per stop a day falls short of its floor share (stops ÷ days, capped by the
    # day's capacity). Larger than the travel saved by consolidating, smaller than a must-see.
    day_balance_penalty: int = 10_800
    # Meals (Đợt 3): two FOOD stops served on the same day must start at least this far
    # apart. Longer than either tightened meal window (2.5h), so two FOOD stops can never share
    # one window, and lunch/dinner of a day stay ≥ 3h apart.
    meal_gap_s: int = 3 * 3600
    # Compactness (Đợt 3): extra travel seconds added to arcs between stops of different travel
    # areas, so far-apart places (Hải Vân vs Hội An) land on different days when feasible.
    # Kept well below ``drop_penalty_base`` so the penalty only steers day assignment and can
    # never make dropping a chosen stop cheaper than connecting it.
    area_spread_penalty: int = 3_600

    def drop_penalty(self, stop: StopSpec) -> int:
        if stop.lock is not None:
            return self.lock_penalty
        if stop.must_see:
            return self.must_see_penalty
        return max(
            self.drop_penalty_floor,
            self.drop_penalty_base - self.drop_penalty_rank_step * stop.rank,
        )


@dataclass(frozen=True, slots=True)
class SolverInput:
    days: tuple[DaySpec, ...]
    stops: tuple[StopSpec, ...]
    durations: DurationLookup
    params: SolverParams = field(default_factory=SolverParams)
    # Per-day cap of stops per category (``StopSpec.category``); missing = uncapped.
    category_day_caps: Mapping[str, int] = field(default_factory=dict)
    # Per-date leg durations that replace ``durations`` on that date (e.g. the walking duration
    # of a pair whose driving leg a car-free rule restricts; ADR-011 amendment 2026-11-09).
    day_durations: Mapping[date, Mapping[tuple[str, str], int]] = field(default_factory=dict)
    # Per-date departure bans: the arc (origin, destination) may not be departed (origin's visit
    # end) inside any of these ``[start_s, end_s)`` spans; a span covering the whole day removes
    # the arc.
    departure_bans: Mapping[date, Mapping[tuple[str, str], tuple[tuple[int, int], ...]]] = field(
        default_factory=dict
    )


class DropReason(StrEnum):
    CLOSED_ON_ALL_DATES = "CLOSED_ON_ALL_DATES"  # no trip date has a window that fits the visit
    LOCKED_DAY_CLOSED = "LOCKED_DAY_CLOSED"  # locked to a day on which it is closed
    UNREACHABLE = "UNREACHABLE"  # every leg to or from it is unavailable
    NOT_SCHEDULED = "NOT_SCHEDULED"  # feasible, but did not fit (time, windows, penalties)


class SolveStatus(StrEnum):
    SOLVED = "SOLVED"
    NO_SOLUTION = "NO_SOLUTION"


@dataclass(frozen=True, slots=True)
class ScheduledStop:
    key: str
    arrival_s: int  # reached the place
    start_s: int  # visit starts (after waiting for opening, if any)
    departure_s: int
    travel_from_previous_s: int

    @property
    def wait_s(self) -> int:
        return self.start_s - self.arrival_s


@dataclass(frozen=True, slots=True)
class BreakSlot:
    start_s: int
    end_s: int


@dataclass(frozen=True, slots=True)
class DayPlan:
    day_index: int
    date: date
    stops: tuple[ScheduledStop, ...]
    start_departure_s: int
    end_arrival_s: int
    travel_to_end_s: int
    lunch: BreakSlot | None = None


@dataclass(frozen=True, slots=True)
class DroppedStop:
    key: str
    reason: DropReason
    must_see: bool
    locked: bool


@dataclass(frozen=True, slots=True)
class SolverResult:
    status: SolveStatus
    days: tuple[DayPlan, ...]
    dropped: tuple[DroppedStop, ...]
    objective: int | None
    time_limit_reached: bool

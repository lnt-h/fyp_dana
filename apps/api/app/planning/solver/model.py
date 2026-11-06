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

    def __post_init__(self) -> None:
        if not (0 <= self.start_s < self.end_s <= SECONDS_PER_DAY):
            raise ValueError("day window must satisfy 0 <= start < end <= 86400")


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

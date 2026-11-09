"""Selected pool + leg matrix → solved days → preview snapshot + Plan Health (§3.2 steps 5-7).

No I/O and no model output: everything here is deterministic Gonarra code (ADR-011). Times are
local (Asia/Ho_Chi_Minh). Leg values come only from the matrix; an unavailable leg stays
``UNAVAILABLE`` with null distance/duration. A pair whose mode a calendar rule restricts uses the
walking matrix on that date (:mod:`app.planning.leg_modes`), in the solver and in the snapshot.

When no leg can be measured at all (no routing provider configured) the strict solve cannot place
anything, because unavailable arcs are forbidden. The scheduler then re-solves with a fixed
*scheduling-only* buffer for unavailable legs so the traveler still gets an ordered plan; those
legs are returned ``UNAVAILABLE`` and Plan Health reports ``LEG_UNAVAILABLE`` (BLOCKED). The
buffer is never shown as a distance or duration (BRU-006).
"""

from __future__ import annotations

import math
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta

from app.planning.calendar.windows import DayWindow
from app.planning.health import (
    HealthConflict,
    HealthDay,
    HealthLeg,
    HealthPlan,
    HealthResult,
    HealthStop,
)
from app.planning.leg_modes import LegModePlan
from app.planning.pool import PoolPlace
from app.planning.solver import (
    DaySpec,
    Interval,
    Lock,
    SolverInput,
    SolverParams,
    SolverResult,
    StopSpec,
    solve,
)
from app.routing.matrix import RouteMatrix
from app.routing.provider import TravelMode
from app.schemas.trips import Conflict
from app.trips.snapshot import SnapshotDay, SnapshotLeg, SnapshotStop

# Scheduling preference (not a fact): FOOD stops are placed at lunch or dinner time.
# Tightened 2026-11-09 (Đợt 3): lunch ends 13:30 and dinner ends 20:00 so the two meals of a
# day can never sit ~1h apart — the windows alone force lunch start ≤ 13:30 − visit and dinner
# start ≥ 17:30, i.e. always ≥ 3h apart.
MEAL_WINDOWS_MIN: tuple[tuple[int, int], ...] = ((11 * 60, 13 * 60 + 30), (17 * 60 + 30, 20 * 60))
UNAVAILABLE_BUFFER_S = 30 * 60
GOOGLE_TTL = timedelta(days=30)


@dataclass(frozen=True, slots=True)
class DayFrame:
    day_index: int  # 1-based (contract)
    date: date
    start_min: int
    end_min: int


@dataclass(frozen=True, slots=True)
class LockedStop:
    stop_id: uuid.UUID
    day_index: int  # 1-based
    position: int
    visit_minutes: int


@dataclass(slots=True)
class ScheduleInput:
    frames: Sequence[DayFrame]
    places: Sequence[PoolPlace]  # ranked, best first
    windows: Mapping[tuple[uuid.UUID, date], DayWindow]
    matrix: RouteMatrix
    anchor_key: str
    mode: str
    must_see: frozenset[uuid.UUID] = frozenset()
    locks: Mapping[uuid.UUID, LockedStop] = field(default_factory=dict)  # by place_id
    params: SolverParams = field(default_factory=SolverParams)
    # Day balance (pace): hard cap of stops per day (raised for locks and must-sees) and a soft
    # fair share per day so no requested day stays empty while candidates exist.
    max_stops_per_day: int | None = None
    # Variety: soft cap of stops per category per day (absent category = uncapped).
    category_day_caps: Mapping[str, int] = field(default_factory=dict)
    # Restricted travel modes (car-free zones): WALK pairs and departure bans per date.
    leg_modes: LegModePlan = field(default_factory=LegModePlan)


@dataclass(frozen=True, slots=True)
class ScheduleOutput:
    result: SolverResult
    buffered: bool  # unavailable legs were scheduled with the scheduling-only buffer


def _intersect(
    spans: Sequence[tuple[int, int]], allowed: Sequence[tuple[int, int]]
) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for start, end in spans:
        for lo, hi in allowed:
            s, e = max(start, lo), min(end, hi)
            if s < e:
                out.append((s, e))
    return sorted(out)


def solver_windows(
    place: PoolPlace,
    frames: Sequence[DayFrame],
    windows: Mapping[tuple[uuid.UUID, date], DayWindow],
) -> dict[date, tuple[Interval, ...]]:
    result: dict[date, tuple[Interval, ...]] = {}
    for frame in frames:
        window = windows.get((place.place_id, frame.date))
        spans = list(window.intervals) if window is not None else []
        if place.category_code == "FOOD":
            spans = _intersect(spans, MEAL_WINDOWS_MIN)
        result[frame.date] = tuple(Interval(s * 60, e * 60) for s, e in spans)
    return result


def ticket_groups(
    places: Sequence[PoolPlace],
    frames: Sequence[DayFrame],
    windows: Mapping[tuple[uuid.UUID, date], DayWindow],
) -> dict[str, str]:
    """Stop key → ticket group, for tickets valid only on their day of purchase.

    The solver keeps the stops of one group on a single day (``StopSpec.ticket_group``), so a
    plan never buys the Hội An Old Town ticket twice (TICKET_VALIDITY, ADR-011).
    """
    groups: dict[str, str] = {}
    for place in places:
        for frame in frames:
            window = windows.get((place.place_id, frame.date))
            if window is None:
                continue
            for notice in window.notices:
                if notice.conflict_type == "TICKET_VALIDITY" and notice.ticket_valid_same_day:
                    groups[place.key] = f"ticket:{notice.rule_id}"
    return groups


def schedule(inp: ScheduleInput) -> ScheduleOutput:
    days = tuple(
        DaySpec(
            date=frame.date,
            start_s=frame.start_min * 60,
            end_s=frame.end_min * 60,
            start_key=inp.anchor_key,
            end_key=inp.anchor_key,
        )
        for frame in inp.frames
    )
    index_of = {frame.day_index: i for i, frame in enumerate(inp.frames)}
    if inp.max_stops_per_day is not None:
        cap = inp.max_stops_per_day
        locked_per_day = [
            sum(1 for lock in inp.locks.values() if index_of.get(lock.day_index) == i)
            for i in range(len(days))
        ]
        must_share = -(-len(inp.must_see) // max(1, len(days)))
        days = tuple(
            replace(day, max_stops=max(cap, locked_per_day[i], must_share))
            for i, day in enumerate(days)
        )
    stops = []
    groups = ticket_groups(inp.places, inp.frames, inp.windows)
    for rank, place in enumerate(inp.places):
        locked = inp.locks.get(place.place_id)
        stops.append(
            StopSpec(
                key=place.key,
                visit_minutes=locked.visit_minutes if locked else place.visit_minutes,
                windows=solver_windows(place, inp.frames, inp.windows),
                rank=rank,
                must_see=place.place_id in inp.must_see,
                lock=Lock(index_of[locked.day_index], locked.position) if locked else None,
                category=place.category_code,
                area=place.area_code,
                ticket_group=groups.get(place.key),
            )
        )
    walk_durations = inp.leg_modes.walk_durations_s()
    bans = inp.leg_modes.bans_s()
    strict = SolverInput(
        days=days,
        stops=tuple(stops),
        durations=inp.matrix.duration_s,
        params=inp.params,
        category_day_caps=inp.category_day_caps,
        day_durations=walk_durations,
        departure_bans=bans,
    )
    result = solve(strict) if stops else _empty(days)
    if stops and not any(plan.stops for plan in result.days) and not _any_available(inp.matrix):

        def buffered(a: str, b: str) -> int:
            value = inp.matrix.duration_s(a, b)
            return UNAVAILABLE_BUFFER_S if value is None else value

        loose = SolverInput(
            days=days,
            stops=tuple(stops),
            durations=buffered,
            params=inp.params,
            category_day_caps=inp.category_day_caps,
            day_durations=walk_durations,
            departure_bans=bans,
        )
        return ScheduleOutput(solve(loose), buffered=True)
    return ScheduleOutput(result, buffered=False)


def _any_available(matrix: RouteMatrix) -> bool:
    return any(leg.available for leg in matrix.legs.values())


def _empty(days: tuple[DaySpec, ...]) -> SolverResult:
    return solve(SolverInput(days=days, stops=(), durations=lambda a, b: 0))


def _clock(seconds: int) -> time:
    seconds = max(0, min(seconds, 24 * 3600 - 60))
    return time(seconds // 3600, (seconds % 3600) // 60)


@dataclass(frozen=True, slots=True)
class ProviderIds:
    google_routes: uuid.UUID | None
    estimate: uuid.UUID | None


def build_days(
    inp: ScheduleInput,
    output: ScheduleOutput,
    *,
    provider_ids: ProviderIds,
    now: datetime,
    stop_ids: Mapping[uuid.UUID, uuid.UUID] | None = None,
) -> list[SnapshotDay]:
    """Snapshot days: stops in solver order, legs between consecutive stops from the matrix.

    ``stop_ids`` keeps existing stop ids per place (day regeneration); new stops get fresh ids.
    """
    places = {place.key: place for place in inp.places}
    mode: TravelMode = "WALK" if inp.mode == "WALK" else "DRIVE"
    snapshot_days: list[SnapshotDay] = []
    for frame, plan in zip(inp.frames, output.result.days, strict=True):
        stops: list[SnapshotStop] = []
        keys: list[str] = []
        for ordinal, scheduled in enumerate(plan.stops, start=1):
            place = places[scheduled.key]
            start_min = scheduled.start_s // 60
            end_min = min(24 * 60 - 1, max(start_min + 1, math.ceil(scheduled.departure_s / 60)))
            stops.append(
                SnapshotStop(
                    id=(stop_ids or {}).get(place.place_id) or uuid.uuid4(),
                    place_id=place.place_id,
                    catalog_publication_id=place.catalog_publication_id,
                    ordinal=ordinal,
                    planned_arrival=_clock(start_min * 60),
                    planned_departure=_clock(end_min * 60),
                    visit_minutes=max(1, min(600, end_min - start_min)),
                    is_locked=place.place_id in inp.locks,
                )
            )
            keys.append(scheduled.key)
        legs = []
        for (a, b), (key_a, key_b) in zip(
            zip(stops, stops[1:], strict=False), zip(keys, keys[1:], strict=False), strict=True
        ):
            walk_matrix = inp.leg_modes.walk_matrix
            if walk_matrix is not None and inp.leg_modes.walks(frame.date, (key_a, key_b)):
                # A rule restricts the plan's mode here: the solver used the walking leg.
                legs.append(_leg(walk_matrix, a.id, b.id, key_a, key_b, "WALK", provider_ids, now))
            else:
                legs.append(_leg(inp.matrix, a.id, b.id, key_a, key_b, mode, provider_ids, now))
        snapshot_days.append(
            SnapshotDay(
                day_index=frame.day_index,
                day_window_start=_clock(frame.start_min * 60),
                day_window_end=_clock(frame.end_min * 60),
                stops=stops,
                legs=legs,
            )
        )
    return snapshot_days


def _leg(
    matrix: RouteMatrix,
    from_id: uuid.UUID,
    to_id: uuid.UUID,
    key_a: str,
    key_b: str,
    mode: TravelMode,
    provider_ids: ProviderIds,
    now: datetime,
) -> SnapshotLeg:
    leg = matrix.leg(key_a, key_b)
    provider = None
    if leg.available and leg.distance_m is not None and leg.duration_s is not None:
        provider = provider_ids.estimate if leg.estimated else provider_ids.google_routes
    if provider is None:
        return SnapshotLeg(
            from_stop_id=from_id, to_stop_id=to_id, travel_mode=mode, availability="UNAVAILABLE"
        )
    return SnapshotLeg(
        from_stop_id=from_id,
        to_stop_id=to_id,
        travel_mode=mode,
        availability="AVAILABLE",
        distance_m=leg.distance_m,
        duration_s=leg.duration_s,
        data_provider_id=provider,
        measured_at=now,
        expires_at=None if leg.estimated else now + GOOGLE_TTL,
        estimated=leg.estimated,
    )


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def health_plan(
    days: Sequence[SnapshotDay],
    dates: Mapping[int, date],
    *,
    pool: Mapping[uuid.UUID, PoolPlace],
    must_see: Sequence[uuid.UUID] = (),
) -> HealthPlan:
    """Plan Health input for a whole snapshot (every day, as planned)."""
    health_days: list[HealthDay] = []
    for day in days:
        stops = tuple(
            HealthStop(
                stop_id=stop.id,
                place_id=stop.place_id,
                arrival_min=_minutes(stop.planned_arrival),
                departure_min=_minutes(stop.planned_departure),
                trust_level=stop.trust_level,
                must_see=stop.place_id in must_see,
                fact_verified_at=(
                    pool[stop.place_id].fact_verified_at
                    if stop.place_id is not None and stop.place_id in pool
                    else None
                ),
            )
            for stop in day.stops
        )
        legs = tuple(
            HealthLeg(
                leg.from_stop_id,
                leg.to_stop_id,
                leg.travel_mode,
                leg.availability,
                leg.duration_s,
                estimated=leg.estimated,
            )
            for leg in day.legs
        )
        start, end = _minutes(day.day_window_start), _minutes(day.day_window_end)
        health_days.append(
            HealthDay(
                date=dates[day.day_index],
                start_min=start,
                end_min=max(end, start + 1),
                stops=stops,
                legs=legs,
            )
        )
    return HealthPlan(days=tuple(health_days), must_see_place_ids=tuple(dict.fromkeys(must_see)))


def to_conflict(conflict: HealthConflict) -> Conflict:
    return Conflict(
        type=conflict.type,
        severity=conflict.severity,
        message=conflict.message,
        rule_id=conflict.rule_id,
        date=conflict.date,
        stop_ids=list(conflict.stop_ids),
    )


def attach_conflicts(days: list[SnapshotDay], health: HealthResult) -> list[Conflict]:
    """Replace every stop/leg conflict with ``health``: single-stop conflicts go on the stop,
    two-stop leg conflicts on the leg; everything else (day window, must-see, multi-stop
    tickets) is returned as plan-level health reasons."""
    for day in days:
        for stop in day.stops:
            stop.conflicts.clear()
        for leg in day.legs:
            leg.conflicts.clear()
    stops = {stop.id: stop for day in days for stop in day.stops}
    legs = {(leg.from_stop_id, leg.to_stop_id): leg for day in days for leg in day.legs}
    plan_level: list[Conflict] = []
    for conflict in health.conflicts:
        item = to_conflict(conflict)
        ids = conflict.stop_ids
        if len(ids) == 1 and ids[0] in stops:
            stops[ids[0]].conflicts.append(item)
        elif len(ids) == 2 and (ids[0], ids[1]) in legs and conflict.type.startswith("LEG_"):
            legs[(ids[0], ids[1])].conflicts.append(item)
        else:
            plan_level.append(item)
    return plan_level

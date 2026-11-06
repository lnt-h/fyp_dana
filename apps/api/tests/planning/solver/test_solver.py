"""OR-Tools multi-day solver on synthetic Đà Nẵng-like instances (ADR-011)."""

from __future__ import annotations

import math
import random
import time
from dataclasses import replace
from datetime import date, timedelta

import pytest

from app.planning.solver import (
    BreakSpec,
    DaySpec,
    DropReason,
    Interval,
    Lock,
    SolverInput,
    SolverParams,
    SolverResult,
    SolveStatus,
    StopSpec,
    regenerate_day,
    solve,
)

H = 3600
START = date(2026, 12, 4)
ANCHOR = "anchor:dn-dragon-bridge"
ANCHOR_POINT = (16.0610, 108.2272)


def _points(n: int, seed: int) -> dict[str, tuple[float, float]]:
    rng = random.Random(seed)
    pts = {ANCHOR: ANCHOR_POINT}
    for i in range(n):
        pts[f"place:p{i:02d}"] = (
            16.0 + rng.uniform(-0.06, 0.06),
            108.22 + rng.uniform(-0.05, 0.05),
        )
    return pts


def _durations(pts: dict[str, tuple[float, float]], forbidden: set[tuple[str, str]] = frozenset()):  # type: ignore[assignment]
    def lookup(a: str, b: str) -> int | None:
        if (a, b) in forbidden:
            return None
        (la, ga), (lb, gb) = pts[a], pts[b]
        dy = (la - lb) * 111_000
        dx = (ga - gb) * 111_000 * math.cos(math.radians(16))
        return int(math.hypot(dx, dy) * 1.35 / (25_000 / 3600)) + 120

    return lookup


def _days(n: int, *, lunch: bool = False) -> tuple[DaySpec, ...]:
    return tuple(
        DaySpec(
            date=START + timedelta(days=i),
            start_s=8 * H,
            end_s=20 * H,
            start_key=ANCHOR,
            end_key=ANCHOR,
            lunch=BreakSpec(11 * H + 1800, 13 * H, H) if lunch else None,
        )
        for i in range(n)
    )


def _open_all(n_days: int, start_h: int = 7, end_h: int = 21) -> dict[date, tuple[Interval, ...]]:
    return {START + timedelta(days=i): (Interval(start_h * H, end_h * H),) for i in range(n_days)}


def _instance(n_stops: int, n_days: int, seed: int = 7, **kw: object) -> SolverInput:
    pts = _points(n_stops, seed)
    rng = random.Random(seed + 1)
    stops = tuple(
        StopSpec(
            key=f"place:p{i:02d}",
            visit_minutes=rng.choice([45, 60, 90, 120]),
            windows=_open_all(n_days),
            rank=i,
        )
        for i in range(n_stops)
    )
    return SolverInput(
        days=_days(n_days, lunch=bool(kw.get("lunch"))),
        stops=stops,
        durations=_durations(pts),
        params=SolverParams(time_limit_s=2.0),
    )


def _scheduled(result: SolverResult) -> dict[str, tuple[int, int, int]]:
    """key -> (day_index, start_s, departure_s)"""
    return {
        s.key: (plan.day_index, s.start_s, s.departure_s)
        for plan in result.days
        for s in plan.stops
    }


def _assert_consistent(inp: SolverInput, result: SolverResult) -> None:
    assert result.status is SolveStatus.SOLVED
    stops = {s.key: s for s in inp.stops}
    seen: set[str] = set()
    for plan in result.days:
        day = inp.days[plan.day_index]
        prev_departure = plan.start_departure_s
        prev_key = day.start_key
        for s in plan.stops:
            assert s.key not in seen
            seen.add(s.key)
            leg = inp.durations(prev_key, s.key)
            assert leg is not None
            assert s.arrival_s >= prev_departure + leg - 1
            assert s.start_s >= s.arrival_s
            assert s.departure_s == s.start_s + stops[s.key].visit_s
            windows = stops[s.key].windows.get(day.date, ())
            assert any(w.start_s <= s.start_s and s.departure_s <= w.end_s for w in windows)
            assert day.start_s <= s.start_s and s.departure_s <= day.end_s
            prev_departure, prev_key = s.departure_s, s.key
        assert plan.end_arrival_s <= day.end_s
    dropped = {d.key for d in result.dropped}
    assert seen.isdisjoint(dropped)
    assert seen | dropped == set(stops)


@pytest.mark.parametrize(("n_stops", "n_days"), [(10, 1), (20, 2), (30, 3)])
def test_feasible_schedule_respects_windows(n_stops: int, n_days: int) -> None:
    inp = _instance(n_stops, n_days)
    result = solve(inp)
    _assert_consistent(inp, result)
    assert len(result.days) == n_days
    assert sum(len(p.stops) for p in result.days) >= min(n_stops, 4 * n_days)


def test_narrow_and_split_windows_are_respected() -> None:
    inp = _instance(12, 1)
    day = inp.days[0].date
    stops = list(inp.stops)
    # Morning-only market, split-hours museum (closed at lunch), evening-only night market.
    stops[0] = replace(stops[0], visit_minutes=60, windows={day: (Interval(6 * H, 10 * H),)})
    stops[1] = replace(
        stops[1],
        visit_minutes=60,
        windows={day: (Interval(8 * H, 11 * H), Interval(14 * H, 17 * H))},
    )
    stops[2] = replace(stops[2], visit_minutes=60, windows={day: (Interval(17 * H, 22 * H),)})
    for i in range(3):
        stops[i] = replace(stops[i], must_see=True)
    inp = replace(inp, stops=tuple(stops))
    result = solve(inp)
    _assert_consistent(inp, result)
    sched = _scheduled(result)
    assert sched["place:p00"][2] <= 10 * H
    museum = sched["place:p01"]
    assert museum[2] <= 11 * H or museum[1] >= 14 * H
    assert sched["place:p02"][1] >= 17 * H


def test_stop_closed_on_a_date_is_not_served_that_day() -> None:
    inp = _instance(20, 3)
    stops = list(inp.stops)
    d0, d1, d2 = (START + timedelta(days=i) for i in range(3))
    # Closed on days 0 and 2 (weekly closure) → may only appear on day 1.
    stops[0] = replace(stops[0], windows={d1: (Interval(8 * H, 17 * H),)}, must_see=True)
    # Closed on every trip date → dropped with a reason, never scheduled.
    stops[1] = replace(stops[1], windows={d0: (), d1: (), d2: ()})
    inp = replace(inp, stops=tuple(stops))
    result = solve(inp)
    _assert_consistent(inp, result)
    sched = _scheduled(result)
    assert sched["place:p00"][0] == 1
    dropped = {d.key: d for d in result.dropped}
    assert dropped["place:p01"].reason is DropReason.CLOSED_ON_ALL_DATES


def test_window_too_short_for_visit_counts_as_closed() -> None:
    inp = _instance(5, 1)
    day = inp.days[0].date
    stops = list(inp.stops)
    stops[0] = replace(stops[0], visit_minutes=120, windows={day: (Interval(9 * H, 10 * H),)})
    inp = replace(inp, stops=tuple(stops))
    result = solve(inp)
    assert {d.key: d.reason for d in result.dropped}["place:p00"] is DropReason.CLOSED_ON_ALL_DATES


def test_must_see_kept_over_better_ranked_stops() -> None:
    inp = _instance(30, 1)
    stops = list(inp.stops)
    stops[-1] = replace(stops[-1], must_see=True, rank=29)  # worst rank, but must-see
    inp = replace(inp, stops=tuple(stops))
    result = solve(inp)
    _assert_consistent(inp, result)
    assert "place:p29" in _scheduled(result)
    assert result.dropped  # 30 stops do not fit one day; others were dropped instead


def test_dropped_must_see_is_reported() -> None:
    inp = _instance(3, 1)
    day = inp.days[0].date
    stops = list(inp.stops)
    stops[0] = replace(
        stops[0], must_see=True, visit_minutes=600, windows={day: (Interval(8 * H, 21 * H),)}
    )
    stops[1] = replace(
        stops[1], must_see=True, visit_minutes=600, windows={day: (Interval(8 * H, 21 * H),)}
    )
    inp = replace(inp, stops=tuple(stops))
    result = solve(inp)
    dropped = [d for d in result.dropped if d.must_see]
    assert len(dropped) == 1 and dropped[0].reason is DropReason.NOT_SCHEDULED


def test_locked_stops_pinned_to_day_and_ordered() -> None:
    inp = _instance(20, 3)
    stops = list(inp.stops)
    stops[15] = replace(stops[15], lock=Lock(day_index=2, position=0))
    stops[3] = replace(stops[3], lock=Lock(day_index=2, position=1))
    stops[9] = replace(stops[9], lock=Lock(day_index=0, position=0))
    inp = replace(inp, stops=tuple(stops))
    result = solve(inp)
    _assert_consistent(inp, result)
    sched = _scheduled(result)
    assert sched["place:p15"][0] == 2
    assert sched["place:p03"][0] == 2
    assert sched["place:p09"][0] == 0
    assert sched["place:p15"][1] < sched["place:p03"][1]


def test_lock_on_closed_day_is_reported() -> None:
    inp = _instance(5, 2)
    stops = list(inp.stops)
    d1 = START + timedelta(days=1)
    stops[0] = replace(stops[0], windows={d1: (Interval(8 * H, 17 * H),)}, lock=Lock(0, 0))
    inp = replace(inp, stops=tuple(stops))
    result = solve(inp)
    dropped = {d.key: d for d in result.dropped}
    assert dropped["place:p00"].reason is DropReason.LOCKED_DAY_CLOSED
    assert dropped["place:p00"].locked


def test_unavailable_legs_are_forbidden_arcs() -> None:
    pts = _points(8, 3)
    keys = [k for k in pts if k != ANCHOR]
    # p00 has no route from or to anything → unreachable.
    forbidden = {(a, "place:p00") for a in pts} | {("place:p00", b) for b in pts}
    # p01 → p02 unavailable: they must never be consecutive in that direction.
    forbidden |= {("place:p01", "place:p02")}
    stops = tuple(
        StopSpec(key=k, visit_minutes=30, windows=_open_all(1), rank=i, must_see=True)
        for i, k in enumerate(keys)
    )
    inp = SolverInput(days=_days(1), stops=stops, durations=_durations(pts, forbidden))
    result = solve(inp)
    _assert_consistent(inp, result)
    order = [s.key for s in result.days[0].stops]
    assert {d.key: d.reason for d in result.dropped}["place:p00"] is DropReason.UNREACHABLE
    assert all((a, b) != ("place:p01", "place:p02") for a, b in zip(order, order[1:], strict=False))
    assert "place:p01" in order and "place:p02" in order


def test_lunch_break_scheduled_inside_its_window() -> None:
    inp = _instance(12, 2, lunch=True)
    result = solve(inp)
    _assert_consistent(inp, result)
    for plan in result.days:
        assert plan.lunch is not None
        assert 11 * H + 1800 <= plan.lunch.start_s <= 13 * H
        for s in plan.stops:  # no visit overlaps lunch
            assert s.departure_s <= plan.lunch.start_s or s.start_s >= plan.lunch.end_s


def test_same_input_same_output() -> None:
    first = solve(_instance(30, 3, seed=11))
    assert not first.time_limit_reached  # the solution limit, not the clock, ended the search
    for _ in range(2):
        again = solve(_instance(30, 3, seed=11))
        assert again.days == first.days
        assert again.dropped == first.dropped
        assert again.objective == first.objective


def test_time_limit_is_honoured() -> None:
    inp = replace(
        _instance(30, 3, seed=5),
        params=SolverParams(time_limit_s=0.5, solution_limit=10_000_000),
    )
    began = time.monotonic()
    result = solve(inp)
    elapsed = time.monotonic() - began
    assert result.status is SolveStatus.SOLVED
    assert elapsed < 0.5 + 1.0  # model build + one solution step overhead
    assert result.time_limit_reached


def test_regenerate_day_single_vehicle_excludes_other_days() -> None:
    inp = _instance(20, 3)
    stops = list(inp.stops)
    stops[4] = replace(stops[4], lock=Lock(day_index=1, position=0))
    stops[5] = replace(stops[5], lock=Lock(day_index=0, position=0))
    inp = replace(inp, stops=tuple(stops))
    full = solve(inp)
    other_days = {s.key for p in full.days if p.day_index != 1 for s in p.stops}
    result = regenerate_day(inp, day_index=1, exclude_keys=other_days)
    assert result.status is SolveStatus.SOLVED
    assert len(result.days) == 1 and result.days[0].day_index == 1
    keys = {s.key for s in result.days[0].stops}
    assert keys.isdisjoint(other_days)
    assert "place:p04" in keys
    assert "place:p05" not in keys  # locked to another day
    assert result.days[0].date == inp.days[1].date


def test_invalid_input_rejected() -> None:
    inp = _instance(3, 1)
    with pytest.raises(ValueError):
        solve(replace(inp, stops=inp.stops + inp.stops[:1]))
    with pytest.raises(ValueError):
        solve(replace(inp, stops=(replace(inp.stops[0], lock=Lock(5, 0)),)))

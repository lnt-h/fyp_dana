"""Car-free zones are handled in scheduling (ADR-011 amendment 2026-11-09).

A rule restricting DRIVE between two Old Town stops (the operator calendar: Hội An Old Town,
15:00–22:00, PARTIAL) must never produce a BLOCKED plan when a reasonable walk exists, and the
solver must route around the restriction when none does. Plan Health keeps LEG_MODE_RESTRICTED
BLOCKING for a plan that still contains a restricted leg.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, date, datetime

from app.planning.assemble import (
    DayFrame,
    ProviderIds,
    ScheduleInput,
    build_days,
    health_plan,
    schedule,
)
from app.planning.calendar.rules import ClosureRule
from app.planning.calendar.windows import OpeningHours, PlaceRef, effective_windows
from app.planning.health import evaluate
from app.planning.leg_modes import (
    WALK_MAX_DISTANCE_M,
    LegModePlan,
    plan_leg_modes,
    restricted_pairs,
)
from app.planning.pool import PoolPlace, by_id
from app.planning.solver import DaySpec, Interval, SolverInput, StopSpec, regenerate_day, solve
from app.routing.matrix import Leg, LegSource, RouteMatrix

H = 3600
CITY = uuid.UUID(int=0xC1)
DAY = date(2026, 11, 10)  # a Tuesday
NOW = datetime(2026, 11, 9, 3, 0, tzinfo=UTC)
TODAY = date(2026, 11, 9)
ANCHOR = "anchor:hoi-an-test"
ANCHOR_POINT = (15.8790, 108.3300)
SPEED = {"DRIVE": 25_000 / 3600, "WALK": 4_500 / 3600}
PROVIDERS = ProviderIds(google_routes=uuid.UUID(int=0xD1), estimate=uuid.UUID(int=0xD2))

CAR_FREE = ClosureRule.from_mapping(
    {
        "id": uuid.UUID(int=0xCF),
        "city_id": CITY,
        "applies_to": "AREA",
        "area_code": "hoi-an-old-town",
        "rule_kind": "WEEKLY",
        "effect": "PARTIAL",
        "params": {
            "weekdays": [1, 2, 3, 4, 5, 6, 7],
            "from": "15:00",
            "to": "22:00",
            "restricted_modes": ["DRIVE", "TWO_WHEELER"],
        },
    }
)


def place(i: int, area: str, lat: float, lng: float, visit: int = 60) -> PoolPlace:
    return PoolPlace(
        place_id=uuid.UUID(int=0x1000 + i, version=4),
        catalog_publication_id=uuid.UUID(int=0x2000 + i, version=4),
        category_code="HERITAGE",
        area_code=area,
        name_vi=f"Điểm {i}",
        name_en=f"Place {i}",
        summary_vi=None,
        summary_en=None,
        lat=lat,
        lng=lng,
        visit_minutes=visit,
        famous=True,
        hours=OpeningHours.every_day("08:00", "21:30"),
        fact_verified_at=date(2026, 10, 1),
    )


# Two Old Town houses ≈ 330 m apart, a third Old Town stop ≈ 2.2 km away (walk unreasonable).
HOUSE = place(1, "hoi-an-old-town", 15.8770, 108.3260)
BRIDGE = place(2, "hoi-an-old-town", 15.8775, 108.3290)
FAR = place(3, "hoi-an-old-town", 15.8920, 108.3400)
BEACH = place(4, "hoi-an-beaches-islands", 15.9130, 108.3400)


def _metres(a: tuple[float, float], b: tuple[float, float]) -> float:
    dy = (a[0] - b[0]) * 111_000
    dx = (a[1] - b[1]) * 111_000 * math.cos(math.radians(16))
    return math.hypot(dx, dy) * 1.35


def matrix(points: dict[str, tuple[float, float]], mode: str) -> RouteMatrix:
    legs = {}
    for a, pa in points.items():
        for b, pb in points.items():
            if a != b:
                distance = round(_metres(pa, pb))
                legs[(a, b)] = Leg(
                    True, distance, round(distance / SPEED[mode]) + 60, LegSource.PROVIDER
                )
    return RouteMatrix(mode=mode, keys=tuple(points), legs=legs)  # type: ignore[arg-type]


def points(*places: PoolPlace, anchor: bool = True) -> dict[str, tuple[float, float]]:
    out = {ANCHOR: ANCHOR_POINT} if anchor else {}
    out.update({p.key: (p.lat, p.lng) for p in places})
    return out


def windows(*places: PoolPlace) -> dict:  # type: ignore[type-arg]
    return effective_windows(
        base_hours={p.place_id: p.hours for p in places},
        rules=[CAR_FREE],
        places=[PlaceRef(p.place_id, p.area_code, CITY) for p in places],
        dates=[DAY],
    )


def leg_plan(*places: PoolPlace, allowed: tuple[str, ...] = ("WALK", "DRIVE")) -> LegModePlan:
    wins = windows(*places)
    pairs = [(p.key, p.place_id) for p in places]
    restricted = restricted_pairs(pairs, [DAY], wins, "DRIVE")
    return plan_leg_modes(
        restricted,
        mode="DRIVE",
        allowed_modes=allowed,
        walk_matrix=matrix(points(*places, anchor=False), "WALK"),
        walk_restricted=restricted_pairs(pairs, [DAY], wins, "WALK"),
    )


def run(  # type: ignore[no-untyped-def]
    *places: PoolPlace,
    leg_modes: LegModePlan | None,
    start_min: int = 8 * 60,
    end_min: int = 21 * 60,
):
    inp = ScheduleInput(
        frames=[DayFrame(1, DAY, start_min, end_min)],
        places=list(places),
        windows=windows(*places),
        matrix=matrix(points(*places), "DRIVE"),
        anchor_key=ANCHOR,
        mode="DRIVE",
        leg_modes=leg_modes or LegModePlan(),
    )
    output = schedule(inp)
    days = build_days(inp, output, provider_ids=PROVIDERS, now=NOW)
    health = evaluate(
        health_plan(days, {1: DAY}, pool=by_id(list(places))), inp.windows, today=TODAY
    )
    return output, days, health


def test_old_town_pair_in_restricted_hours_walks_and_is_not_blocked() -> None:
    plan = leg_plan(HOUSE, BRIDGE)
    assert plan.walks(DAY, (HOUSE.key, BRIDGE.key)) and plan.walks(DAY, (BRIDGE.key, HOUSE.key))
    # The day starts at 15:00, so the leg departs inside the car-free window.
    output, days, health = run(HOUSE, BRIDGE, leg_modes=plan, start_min=15 * 60)
    stops = [stop.place_id for stop in days[0].stops]
    assert set(stops) == {HOUSE.place_id, BRIDGE.place_id}
    assert all(stop.planned_arrival.hour >= 15 for stop in days[0].stops)
    (leg,) = days[0].legs
    assert leg.travel_mode == "WALK" and leg.availability == "AVAILABLE"
    first, second = (HOUSE, BRIDGE) if stops[0] == HOUSE.place_id else (BRIDGE, HOUSE)
    walk = matrix(points(HOUSE, BRIDGE, anchor=False), "WALK").leg(first.key, second.key)
    # Distance and duration are the walking matrix values, and the solver used the same duration.
    assert (leg.distance_m, leg.duration_s) == (walk.distance_m, walk.duration_s)
    assert output.result.days[0].stops[1].travel_from_previous_s == walk.duration_s
    assert "LEG_MODE_RESTRICTED" not in {c.type for c in health.conflicts}
    assert health.plan_health != "BLOCKED"


def test_without_leg_modes_the_same_plan_is_blocked() -> None:
    """The bug: a DRIVE leg between two Old Town stops in car-free hours."""
    _, days, health = run(HOUSE, BRIDGE, leg_modes=None, start_min=15 * 60)
    assert days[0].legs[0].travel_mode == "DRIVE"
    restricted = [c for c in health.conflicts if c.type == "LEG_MODE_RESTRICTED"]
    assert [(c.severity, c.rule_id) for c in restricted] == [("BLOCKING", CAR_FREE.id)]
    assert health.plan_health == "BLOCKED"


def test_walk_too_far_is_banned_not_walked() -> None:
    plan = leg_plan(HOUSE, FAR)
    walk = matrix(points(HOUSE, FAR, anchor=False), "WALK").leg(HOUSE.key, FAR.key)
    assert walk.distance_m is not None and walk.distance_m > WALK_MAX_DISTANCE_M
    assert not plan.walk
    assert plan.bans[DAY][(HOUSE.key, FAR.key)] == ((15 * 60, 22 * 60),)


def test_no_walk_allowed_solver_avoids_the_restricted_leg() -> None:
    """DRIVE-only traveler: no alternative, so the two zone stops are never chained in the
    car-free window; one is left out and the plan is valid (not BLOCKED)."""
    plan = leg_plan(HOUSE, BRIDGE, allowed=("DRIVE",))
    assert not plan.walk and (HOUSE.key, BRIDGE.key) in plan.bans[DAY]
    output, days, health = run(HOUSE, BRIDGE, leg_modes=plan, start_min=15 * 60)
    assert len(days[0].stops) == 1 and days[0].legs == []
    assert [d.key for d in output.result.dropped] in ([HOUSE.key], [BRIDGE.key])
    assert "LEG_MODE_RESTRICTED" not in {c.type for c in health.conflicts}
    assert health.plan_health != "BLOCKED"


def test_no_alternative_left_in_plan_is_still_blocking() -> None:
    """When a restricted DRIVE leg remains (no valid alternative was applied), Health blocks."""
    plan = leg_plan(HOUSE, BRIDGE, allowed=("DRIVE",))
    assert not plan.walk  # no alternative exists
    _, _, health = run(HOUSE, BRIDGE, leg_modes=None, start_min=15 * 60)
    assert [c.severity for c in health.conflicts if c.type == "LEG_MODE_RESTRICTED"] == ["BLOCKING"]
    assert health.plan_health == "BLOCKED"


def test_mixed_zone_and_outside_stops_only_zone_pairs_walk() -> None:
    plan = leg_plan(HOUSE, BRIDGE, BEACH)
    assert all(BEACH.key not in pair for pairs in plan.walk.values() for pair in pairs)
    _, days, health = run(HOUSE, BRIDGE, BEACH, leg_modes=plan, start_min=15 * 60)
    keys = {p.place_id: p.key for p in (HOUSE, BRIDGE, BEACH)}
    for leg in days[0].legs:
        stops = {s.id: s.place_id for s in days[0].stops}
        a, b = keys[stops[leg.from_stop_id]], keys[stops[leg.to_stop_id]]
        assert leg.travel_mode == ("WALK" if plan.walks(DAY, (a, b)) else "DRIVE")
    assert health.plan_health != "BLOCKED"


# ---- solver level ----------------------------------------------------------------------------


def _solver_input(**extra: object) -> SolverInput:
    window = {DAY: (Interval(13 * H, 21 * H),)}
    stops = (
        StopSpec("x", 60, window, rank=0),
        StopSpec("y", 60, window, rank=1),
    )

    def durations(a: str, b: str) -> int | None:
        return 600

    return SolverInput(
        days=(DaySpec(DAY, 8 * H, 21 * H, "anchor", "anchor"),),
        stops=stops,
        durations=durations,
        **extra,  # type: ignore[arg-type]
    )


def test_solver_uses_date_override_duration() -> None:
    override = {DAY: {("x", "y"): 300, ("y", "x"): 300}}
    result = solve(_solver_input(day_durations=override))
    second = result.days[0].stops[1]
    assert second.travel_from_previous_s == 300
    regenerated = regenerate_day(_solver_input(day_durations=override), day_index=0)
    assert regenerated.days[0].stops[1].travel_from_previous_s == 300


def test_solver_departure_ban_moves_departure_outside_window() -> None:
    # x → y and y → x may not depart between 15:00 and 21:00; windows open from 13:00, so the
    # only way to keep both is to leave the first stop by 14:59 (one-minute margin).
    ban = ((15 * H, 21 * H),)
    result = solve(_solver_input(departure_bans={DAY: {("x", "y"): ban, ("y", "x"): ban}}))
    plan = result.days[0]
    assert len(plan.stops) == 2
    assert plan.stops[0].departure_s <= 15 * H - 60


def test_solver_whole_day_ban_removes_the_arc() -> None:
    ban = ((0, 24 * H),)
    result = solve(_solver_input(departure_bans={DAY: {("x", "y"): ban, ("y", "x"): ban}}))
    assert len(result.days[0].stops) == 1
    assert [d.key for d in result.dropped] == ["y"]

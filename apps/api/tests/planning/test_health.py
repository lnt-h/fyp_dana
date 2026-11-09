"""Plan Health: every contract conflict type, severity, status and deterministic order."""

import uuid
from datetime import date, timedelta
from typing import Any

import pytest

from app.planning.calendar.rules import ClosureRule
from app.planning.calendar.windows import DayWindow, OpeningHours, PlaceRef, effective_windows
from app.planning.health import (
    CONFLICT_SEVERITY,
    HealthDay,
    HealthLeg,
    HealthPlan,
    HealthResult,
    HealthStop,
    evaluate,
)

CITY = uuid.UUID(int=0xC1)
TODAY = date(2026, 11, 6)
MON = date(2026, 11, 9)
TUE = date(2026, 11, 10)
WED = date(2026, 11, 11)
LANTERN = date(2026, 11, 22)  # lunar 14/10, a Sunday
TET = date(2027, 2, 6)

MUSEUM = PlaceRef(uuid.UUID(int=0xA1), "hai-chau", CITY)
BEACH = PlaceRef(uuid.UUID(int=0xA2), "son-tra", CITY)
HOUSE = PlaceRef(uuid.UUID(int=0xA3), "hoi-an-old-town", CITY)
BRIDGE = PlaceRef(uuid.UUID(int=0xA4), "hoi-an-old-town", CITY)
UNKNOWN = PlaceRef(uuid.UUID(int=0xA5), "son-tra", CITY)
PLACES = [MUSEUM, BEACH, HOUSE, BRIDGE, UNKNOWN]
HOURS = {
    MUSEUM.place_id: OpeningHours.every_day("08:00", "17:00"),
    BEACH.place_id: OpeningHours.every_day("05:00", "22:00"),
    HOUSE.place_id: OpeningHours.every_day("08:00", "21:30"),
    BRIDGE.place_id: OpeningHours.every_day("08:00", "21:30"),
    UNKNOWN.place_id: None,
}


def rule(n: int, kind: str, effect: str, params: dict[str, Any], **target: Any) -> ClosureRule:
    data: dict[str, Any] = {
        "id": uuid.UUID(int=n),
        "city_id": CITY,
        "applies_to": "PLACE",
        "place_id": MUSEUM.place_id,
        "rule_kind": kind,
        "effect": effect,
        "params": params,
    }
    data.update(target)
    return ClosureRule.from_mapping(data)


def area(n: int, kind: str, effect: str, params: dict[str, Any]) -> ClosureRule:
    return rule(
        n, kind, effect, params, applies_to="AREA", place_id=None, area_code="hoi-an-old-town"
    )


def wins(rules: list[ClosureRule], dates: list[date]) -> dict[tuple[uuid.UUID, date], DayWindow]:
    return effective_windows(base_hours=HOURS, rules=rules, places=PLACES, dates=dates)


def stop(n: int, place: PlaceRef | None, arrive: str, leave: str, **extra: Any) -> HealthStop:
    def minutes(value: str) -> int:
        hours, mins = value.split(":")
        return int(hours) * 60 + int(mins)

    return HealthStop(
        stop_id=uuid.UUID(int=0x100 + n),
        place_id=place.place_id if place else None,
        arrival_min=minutes(arrive),
        departure_min=minutes(leave),
        **extra,
    )


def leg(
    a: HealthStop,
    b: HealthStop,
    mode: str = "DRIVE",
    availability: str = "AVAILABLE",
    estimated: bool = False,
) -> HealthLeg:
    return HealthLeg(
        a.stop_id,
        b.stop_id,
        mode,  # type: ignore[arg-type]
        availability,  # type: ignore[arg-type]
        600,
        estimated=estimated,
    )


def day(
    on: date,
    *stops: HealthStop,
    legs: tuple[HealthLeg, ...] = (),
    start: int = 480,
    end: int = 1260,
) -> HealthDay:
    return HealthDay(date=on, start_min=start, end_min=end, stops=stops, legs=legs)


def run(plan: HealthPlan, rules: list[ClosureRule] | None = None) -> HealthResult:
    dates = sorted({d.date for d in plan.days})
    return evaluate(plan, wins(rules or [], dates), today=TODAY)


def types(result: HealthResult) -> list[str]:
    return [c.type for c in result.conflicts]


def test_clean_plan_is_good() -> None:
    a = stop(1, MUSEUM, "09:00", "10:30", fact_verified_at=TODAY - timedelta(days=30))
    b = stop(2, BEACH, "11:00", "12:00")
    result = run(HealthPlan(days=(day(TUE, a, b, legs=(leg(a, b),)),)))
    assert result.plan_health == "GOOD"
    assert result.conflicts == ()


def test_severity_table_matches_contract() -> None:
    blocking = {t for t, s in CONFLICT_SEVERITY.items() if s == "BLOCKING"}
    assert blocking == {
        "CLOSED_AT_PLANNED_TIME",
        "CLOSED_ON_DATE",
        "LEG_UNAVAILABLE",
        "LEG_MODE_RESTRICTED",
        "DAY_WINDOW_EXCEEDED",
        "WEB_PLACE_UNRESOLVED",
    }
    # DEC-030: unknown hours are missing data, not a plan problem.
    assert {t for t, s in CONFLICT_SEVERITY.items() if s == "INFO"} == {
        "LEG_ESTIMATED",
        "OPENING_HOURS_UNKNOWN",
    }
    assert len(CONFLICT_SEVERITY) == 14


def test_closed_at_planned_time_outside_hours() -> None:
    late = stop(1, MUSEUM, "16:30", "17:30")
    result = run(HealthPlan(days=(day(TUE, late),)))
    assert types(result) == ["CLOSED_AT_PLANNED_TIME"]
    conflict = result.conflicts[0]
    assert conflict.severity == "BLOCKING" and conflict.rule_id is None
    assert conflict.date == TUE and conflict.stop_ids == (late.stop_id,)
    assert conflict.message_key == "plan_health.conflict.closed_at_planned_time"
    assert conflict.message
    assert result.plan_health == "BLOCKED"


def test_closed_at_planned_time_attributed_to_rule() -> None:
    lunch = rule(1, "WEEKLY", "CLOSED", {"weekdays": [2], "from": "11:30", "to": "13:30"})
    visit = stop(1, MUSEUM, "11:00", "12:00")
    result = run(HealthPlan(days=(day(TUE, visit),)), [lunch])
    assert [(c.type, c.rule_id) for c in result.conflicts] == [("CLOSED_AT_PLANNED_TIME", lunch.id)]
    partial = rule(2, "DATE", "PARTIAL", {"dates": ["2026-11-10"], "from": "13:00", "to": "17:00"})
    result = run(HealthPlan(days=(day(TUE, stop(2, MUSEUM, "09:00", "10:00")),)), [partial])
    assert [(c.type, c.rule_id) for c in result.conflicts] == [
        ("CLOSED_AT_PLANNED_TIME", partial.id)
    ]


def test_closed_on_date_weekly_and_tet() -> None:
    monday = rule(3, "WEEKLY", "CLOSED", {"weekdays": [1]})
    result = run(HealthPlan(days=(day(MON, stop(1, MUSEUM, "09:00", "10:00")),)), [monday])
    assert [(c.type, c.rule_id, c.date) for c in result.conflicts] == [
        ("CLOSED_ON_DATE", monday.id, MON)
    ]
    tet = rule(
        4,
        "LUNAR_DATE",
        "CLOSED",
        {"lunar_days": [1], "lunar_months": [1]},
        applies_to="CITY",
        place_id=None,
    )
    result = run(HealthPlan(days=(day(TET, stop(1, BEACH, "09:00", "10:00")),)), [tet])
    assert [(c.type, c.rule_id, c.date) for c in result.conflicts] == [
        ("CLOSED_ON_DATE", tet.id, TET)
    ]
    assert result.plan_health == "BLOCKED"


def test_closed_on_date_from_regular_hours() -> None:
    hours = {**HOURS, MUSEUM.place_id: OpeningHours.from_value({"2": [["08:00", "17:00"]]})}
    windows = effective_windows(base_hours=hours, rules=[], places=PLACES, dates=[MON])
    plan = HealthPlan(days=(day(MON, stop(1, MUSEUM, "09:00", "10:00")),))
    result = evaluate(plan, windows, today=TODAY)
    assert [(c.type, c.rule_id) for c in result.conflicts] == [("CLOSED_ON_DATE", None)]


def test_opening_hours_unknown_is_info_not_a_closure() -> None:
    early = stop(1, UNKNOWN, "06:00", "07:00")  # outside the scheduling default, still not "closed"
    result = run(HealthPlan(days=(day(TUE, early, start=360),)))
    assert types(result) == ["OPENING_HOURS_UNKNOWN"]
    assert result.conflicts[0].severity == "INFO" and not result.conflicts[0].blocking
    assert result.plan_health == "GOOD"  # DEC-030
    # No window at all (e.g. a web stop without hours) is also unknown.
    result = run(HealthPlan(days=(day(TUE, stop(2, None, "09:00", "10:00")),)))
    assert types(result) == ["OPENING_HOURS_UNKNOWN"]


def test_unknown_hours_still_honour_closure_rules() -> None:
    noon = rule(
        5,
        "WEEKLY",
        "CLOSED",
        {"weekdays": [2], "from": "11:00", "to": "14:00"},
        place_id=UNKNOWN.place_id,
    )
    result = run(HealthPlan(days=(day(TUE, stop(1, UNKNOWN, "12:00", "13:00")),)), [noon])
    assert [(c.type, c.rule_id) for c in result.conflicts] == [
        ("CLOSED_AT_PLANNED_TIME", noon.id),
        ("OPENING_HOURS_UNKNOWN", None),
    ]


def test_leg_unavailable() -> None:
    a, b = stop(1, MUSEUM, "09:00", "10:00"), stop(2, BEACH, "11:00", "12:00")
    for availability in ("UNAVAILABLE", "EXPIRED"):
        result = run(
            HealthPlan(days=(day(TUE, a, b, legs=(leg(a, b, availability=availability),)),))
        )
        assert [(c.type, c.stop_ids) for c in result.conflicts] == [
            ("LEG_UNAVAILABLE", (a.stop_id, b.stop_id))
        ]
        assert result.plan_health == "BLOCKED"


def test_day_window_exceeded() -> None:
    a, b = stop(1, BEACH, "07:00", "08:30"), stop(2, BEACH, "20:30", "21:30")
    ok = stop(3, MUSEUM, "09:00", "10:00")
    result = run(HealthPlan(days=(day(TUE, a, ok, b),)))
    assert [(c.type, c.stop_ids) for c in result.conflicts] == [
        ("DAY_WINDOW_EXCEEDED", (a.stop_id, b.stop_id))
    ]


def test_fact_stale_boundary() -> None:
    fresh = stop(1, MUSEUM, "09:00", "10:00", fact_verified_at=TODAY - timedelta(days=180))
    stale = stop(2, BEACH, "11:00", "12:00", fact_verified_at=TODAY - timedelta(days=181))
    result = run(HealthPlan(days=(day(TUE, fresh, stale),)))
    assert [(c.type, c.stop_ids) for c in result.conflicts] == [("FACT_STALE", (stale.stop_id,))]
    assert result.plan_health == "WARNING"


def test_must_see_not_included() -> None:
    plan = HealthPlan(
        days=(day(TUE, stop(1, MUSEUM, "09:00", "10:00")),),
        must_see_place_ids=(MUSEUM.place_id, HOUSE.place_id, HOUSE.place_id),
    )
    result = run(plan)
    assert [(c.type, c.place_id, c.date, c.stop_ids) for c in result.conflicts] == [
        ("MUST_SEE_NOT_INCLUDED", HOUSE.place_id, None, ())
    ]
    assert result.plan_health == "WARNING"


def test_leg_mode_restricted_inside_car_free_zone_only() -> None:
    car_free = area(
        6, "WEEKLY", "NOTICE", {"weekdays": [1, 2, 3, 4, 5, 6, 7], "restricted_modes": ["DRIVE"]}
    )
    a = stop(1, HOUSE, "09:00", "10:00")
    b = stop(2, BRIDGE, "10:15", "11:00")
    c = stop(3, BEACH, "12:00", "13:00")
    plan = HealthPlan(days=(day(TUE, a, b, c, legs=(leg(a, b, "DRIVE"), leg(b, c, "DRIVE"))),))
    result = run(plan, [car_free])
    restricted = [x for x in result.conflicts if x.type == "LEG_MODE_RESTRICTED"]
    assert [(x.stop_ids, x.rule_id) for x in restricted] == [((a.stop_id, b.stop_id), car_free.id)]
    # Walking inside the zone is fine; the notice itself (SEASONAL_WARNING) remains a warning.
    plan = HealthPlan(days=(day(TUE, a, b, legs=(leg(a, b, "WALK"),)),))
    assert "LEG_MODE_RESTRICTED" not in types(run(plan, [car_free]))


def test_leg_mode_restricted_only_inside_rule_time_range() -> None:
    evening = area(
        7,
        "WEEKLY",
        "NOTICE",
        {"weekdays": [2], "from": "18:00", "to": "22:00", "restricted_modes": ["DRIVE"]},
    )
    a, b = stop(1, HOUSE, "17:00", "18:30"), stop(2, BRIDGE, "18:45", "19:30")
    early_a, early_b = stop(3, HOUSE, "09:00", "10:00"), stop(4, BRIDGE, "10:15", "11:00")
    result = run(HealthPlan(days=(day(TUE, a, b, legs=(leg(a, b),)),)), [evening])
    assert "LEG_MODE_RESTRICTED" in types(result)
    result = run(
        HealthPlan(days=(day(TUE, early_a, early_b, legs=(leg(early_a, early_b),)),)), [evening]
    )
    assert types(result) == []


def test_lunar_event_conflict_on_lantern_night_overlap_only() -> None:
    lantern = area(8, "LUNAR_DATE", "EVENT", {"lunar_days": [14], "from": "18:00", "to": "22:00"})
    night = stop(1, HOUSE, "19:00", "20:00")
    morning = stop(2, BRIDGE, "09:00", "10:00")
    result = run(HealthPlan(days=(day(LANTERN, morning, night),)), [lantern])
    assert [(c.type, c.rule_id, c.date, c.stop_ids) for c in result.conflicts] == [
        ("LUNAR_EVENT_CONFLICT", lantern.id, LANTERN, (night.stop_id,))
    ]
    assert result.plan_health == "WARNING"
    # The day after is not lunar 14.
    other = run(HealthPlan(days=(day(LANTERN + timedelta(days=1), night),)), [lantern])
    assert other.conflicts == ()


def test_seasonal_warning() -> None:
    rainy = rule(
        9,
        "SEASON",
        "NOTICE",
        {"from_month_day": "09-01", "to_month_day": "12-31"},
        place_id=BEACH.place_id,
    )
    result = run(HealthPlan(days=(day(TUE, stop(1, BEACH, "09:00", "10:00")),)), [rainy])
    assert [(c.type, c.rule_id, c.severity) for c in result.conflicts] == [
        ("SEASONAL_WARNING", rainy.id, "WARNING")
    ]


def test_ticket_validity_same_day() -> None:
    ticket = area(10, "TICKET_VALIDITY", "NOTICE", {"valid_same_day": True})
    d1 = stop(1, HOUSE, "09:00", "10:00")
    d1b = stop(2, BRIDGE, "10:30", "11:00")
    d2 = stop(3, BRIDGE, "09:00", "10:00")
    one_day = HealthPlan(days=(day(TUE, d1, d1b),))
    assert run(one_day, [ticket]).conflicts == ()
    two_days = HealthPlan(days=(day(TUE, d1, d1b), day(WED, d2)))
    result = run(two_days, [ticket])
    assert [(c.type, c.rule_id, c.date, c.stop_ids) for c in result.conflicts] == [
        ("TICKET_VALIDITY", ticket.id, WED, (d2.stop_id,))
    ]


def test_ticket_validity_hours() -> None:
    ticket = area(11, "TICKET_VALIDITY", "NOTICE", {"valid_hours": 24})
    d1 = stop(1, HOUSE, "15:00", "16:00")
    d2_ok = stop(2, BRIDGE, "09:00", "10:00")
    d2_late = stop(3, HOUSE, "15:30", "16:30")
    result = run(HealthPlan(days=(day(TUE, d1), day(WED, d2_ok, d2_late))), [ticket])
    assert [(c.type, c.date, c.stop_ids) for c in result.conflicts] == [
        ("TICKET_VALIDITY", WED, (d2_late.stop_id,))
    ]


def test_web_place_unverified_caps_at_warning() -> None:
    web = stop(1, None, "09:00", "10:00", trust_level="WEB_UNVERIFIED")
    windows = wins([], [TUE])
    key = uuid.UUID(int=0xBEEF)
    windows[(key, TUE)] = DayWindow(
        place_id=key,
        date=TUE,
        intervals=((480, 1020),),
        unknown_hours=False,
        base_intervals=((480, 1020),),
    )
    keyed = stop(2, PlaceRef(key), "11:00", "12:00", trust_level="WEB_UNVERIFIED")
    result = evaluate(HealthPlan(days=(day(TUE, keyed),)), windows, today=TODAY)
    assert types(result) == ["WEB_PLACE_UNVERIFIED"]
    assert result.plan_health == "WARNING"
    result = evaluate(HealthPlan(days=(day(TUE, web),)), windows, today=TODAY)
    assert types(result) == ["OPENING_HOURS_UNKNOWN", "WEB_PLACE_UNVERIFIED"]


def test_web_place_unresolved_blocks() -> None:
    web = stop(1, None, "09:00", "10:00", trust_level="WEB_UNVERIFIED", web_resolved=False)
    result = run(HealthPlan(days=(day(TUE, web),)))
    assert "WEB_PLACE_UNRESOLVED" in types(result)
    assert result.plan_health == "BLOCKED"


def test_estimated_leg_is_info_and_keeps_plan_good() -> None:
    a = stop(1, MUSEUM, "09:00", "10:30")
    b = stop(2, BEACH, "11:00", "12:00")
    result = run(HealthPlan(days=(day(TUE, a, b, legs=(leg(a, b, estimated=True),)),)))
    assert types(result) == ["LEG_ESTIMATED"]
    (notice,) = result.conflicts
    assert notice.severity == "INFO" and not notice.blocking
    assert notice.stop_ids == (a.stop_id, b.stop_id)
    assert notice.message_key == "plan_health.conflict.leg_estimated"
    assert result.plan_health == "GOOD"


def test_unknown_hours_and_estimated_legs_only_is_good() -> None:
    """DEC-030: a plan whose only issues are missing hours and estimated legs is GOOD."""
    unknown_hours = {place.place_id: None for place in PLACES}
    a = stop(1, MUSEUM, "09:00", "10:30")
    b = stop(2, BEACH, "11:00", "12:00")
    c = stop(3, UNKNOWN, "13:00", "14:00")
    plan = HealthPlan(
        days=(day(TUE, a, b, c, legs=(leg(a, b, estimated=True), leg(b, c, estimated=True))),)
    )
    windows = effective_windows(base_hours=unknown_hours, rules=[], places=PLACES, dates=[TUE])
    result = evaluate(plan, windows, today=TODAY)
    assert sorted(types(result)) == ["LEG_ESTIMATED"] * 2 + ["OPENING_HOURS_UNKNOWN"] * 3
    assert {c.severity for c in result.conflicts} == {"INFO"}
    assert result.plan_health == "GOOD"


def test_estimated_flag_ignored_on_unavailable_leg() -> None:
    a = stop(1, MUSEUM, "09:00", "10:30")
    b = stop(2, BEACH, "11:00", "12:00")
    unavailable = leg(a, b, availability="UNAVAILABLE", estimated=True)
    result = run(HealthPlan(days=(day(TUE, a, b, legs=(unavailable,)),)))
    assert types(result) == ["LEG_UNAVAILABLE"] and result.plan_health == "BLOCKED"


def test_all_14_types_and_deterministic_order() -> None:
    rules = [
        rule(20, "WEEKLY", "CLOSED", {"weekdays": [1]}),  # museum closed Mondays
        area(21, "LUNAR_DATE", "EVENT", {"lunar_days": [14]}),
        area(22, "TICKET_VALIDITY", "NOTICE", {"valid_same_day": True}),
        area(23, "WEEKLY", "NOTICE", {"weekdays": [7], "restricted_modes": ["DRIVE"]}),
        rule(
            24,
            "SEASON",
            "NOTICE",
            {"from_month_day": "11-01", "to_month_day": "11-30"},
            place_id=BEACH.place_id,
        ),
    ]
    sat = LANTERN - timedelta(days=1)
    mon_closed = stop(1, MUSEUM, "09:00", "10:00")
    mon_late = stop(2, BEACH, "21:00", "21:45", fact_verified_at=date(2025, 1, 1))
    sat_house = stop(3, HOUSE, "09:00", "10:00")
    sun_house = stop(4, HOUSE, "09:00", "10:00")
    sun_bridge = stop(5, BRIDGE, "10:30", "11:00")
    sun_unknown = stop(6, UNKNOWN, "12:00", "13:00")
    sun_web = stop(7, None, "14:00", "15:00", trust_level="WEB_UNVERIFIED")
    sun_bad_web = stop(8, None, "15:30", "16:00", trust_level="WEB_UNVERIFIED", web_resolved=False)
    sun_museum = stop(9, MUSEUM, "16:30", "17:30")
    plan = HealthPlan(
        days=(
            day(
                MON,
                mon_closed,
                mon_late,
                legs=(leg(mon_closed, mon_late, availability="UNAVAILABLE"),),
                end=1260,
            ),
            day(sat, sat_house),
            day(
                LANTERN,
                sun_house,
                sun_bridge,
                sun_unknown,
                sun_web,
                sun_bad_web,
                sun_museum,
                legs=(leg(sun_house, sun_bridge, estimated=True),),
            ),
        ),
        must_see_place_ids=(uuid.UUID(int=0xF00D),),
    )
    dates = [MON, sat, LANTERN]
    windows = wins(rules, dates)
    first = evaluate(plan, windows, today=TODAY)
    second = evaluate(plan, dict(reversed(list(windows.items()))), today=TODAY)
    assert first == second
    assert set(types(first)) == set(CONFLICT_SEVERITY)
    keys = [
        (c.date is None, c.date or date.min, list(CONFLICT_SEVERITY).index(c.type))
        for c in first.conflicts
    ]
    assert keys == sorted(keys)
    assert first.plan_health == "BLOCKED"
    assert len(first.blocking) == sum(1 for c in first.conflicts if c.severity == "BLOCKING")
    # Every calendar conflict carries its rule id and date.
    for conflict in first.conflicts:
        if conflict.type in {
            "LUNAR_EVENT_CONFLICT",
            "TICKET_VALIDITY",
            "SEASONAL_WARNING",
            "LEG_MODE_RESTRICTED",
        }:
            assert conflict.rule_id is not None and conflict.date is not None


def test_invalid_inputs_rejected() -> None:
    with pytest.raises(ValueError):
        stop(1, MUSEUM, "10:00", "09:00")
    a, b = stop(1, MUSEUM, "09:00", "10:00"), stop(2, BEACH, "11:00", "12:00")
    with pytest.raises(ValueError):
        HealthDay(date=TUE, start_min=480, end_min=1260, stops=(a,), legs=(leg(a, b),))
    with pytest.raises(ValueError):
        HealthDay(date=TUE, start_min=600, end_min=600)
    with pytest.raises(ValueError):
        HealthDay(date=TUE, start_min=480, end_min=1260, stops=(a, a))

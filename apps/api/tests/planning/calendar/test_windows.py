"""Effective windows: opening hours × closure rules per (place, date) (ADR-011 0.3)."""

import uuid
from datetime import date
from typing import Any

import pytest

from app.planning.calendar.rules import ClosureRule
from app.planning.calendar.windows import (
    DEFAULT_UNKNOWN_HOURS_WINDOW,
    OpeningHours,
    PlaceRef,
    effective_windows,
    rule_targets,
)

CITY = uuid.UUID(int=0xC1)
OTHER_CITY = uuid.UUID(int=0xC2)
MUSEUM = PlaceRef(uuid.UUID(int=0xA1), area_code="hai-chau", city_id=CITY)
OLD_HOUSE = PlaceRef(uuid.UUID(int=0xA2), area_code="hoi-an-old-town", city_id=CITY)
NO_HOURS = PlaceRef(uuid.UUID(int=0xA3), area_code="son-tra", city_id=CITY)

HOURS = OpeningHours.every_day("08:00", "17:00")
MON = date(2026, 11, 9)
TUE = date(2026, 11, 10)
TET_2026 = date(2026, 2, 17)
LANTERN = date(2026, 11, 22)  # lunar 14/10


def make(
    rule_id: int, kind: str, effect: str, params: dict[str, Any], **target: Any
) -> ClosureRule:
    data: dict[str, Any] = {
        "id": uuid.UUID(int=rule_id),
        "city_id": CITY,
        "applies_to": "PLACE",
        "place_id": MUSEUM.place_id,
        "rule_kind": kind,
        "effect": effect,
        "severity": "BLOCKING" if effect == "CLOSED" else "WARNING",
        "params": params,
    }
    data.update(target)
    return ClosureRule.from_mapping(data)


def windows(
    rules: list[ClosureRule], dates: list[date], places: list[PlaceRef] | None = None
) -> dict[tuple[uuid.UUID, date], Any]:
    return effective_windows(
        base_hours={MUSEUM.place_id: HOURS, OLD_HOUSE.place_id: HOURS, NO_HOURS.place_id: None},
        rules=rules,
        places=places or [MUSEUM],
        dates=dates,
    )


def test_no_rules_gives_opening_hours() -> None:
    window = windows([], [MON])[(MUSEUM.place_id, MON)]
    assert window.intervals == ((480, 1020),)
    assert not window.unknown_hours and not window.is_closed
    assert window.notices == () and window.closed_rule_ids == ()


def test_weekly_closed_removes_the_day() -> None:
    closed = make(1, "WEEKLY", "CLOSED", {"weekdays": [1]})
    result = windows([closed], [MON, TUE])
    assert result[(MUSEUM.place_id, MON)].is_closed
    assert result[(MUSEUM.place_id, MON)].closed_rule_ids == (closed.id,)
    assert result[(MUSEUM.place_id, TUE)].intervals == ((480, 1020),)


def test_lunar_tet_closure_city_wide() -> None:
    tet = make(
        2,
        "LUNAR_DATE",
        "CLOSED",
        {"lunar_days": [1, 2, 3], "lunar_months": [1]},
        applies_to="CITY",
        place_id=None,
    )
    result = windows([tet], [TET_2026], [MUSEUM, OLD_HOUSE, NO_HOURS])
    assert all(w.is_closed for w in result.values())
    assert result[(NO_HOURS.place_id, TET_2026)].unknown_hours


def test_closed_with_time_range_subtracts() -> None:
    lunch = make(3, "WEEKLY", "CLOSED", {"weekdays": [2], "from": "11:30", "to": "13:30"})
    window = windows([lunch], [TUE])[(MUSEUM.place_id, TUE)]
    assert window.intervals == ((480, 690), (810, 1020))
    assert window.closed_rule_ids == ()
    assert window.adjustments[0].rule_id == lunch.id


def test_partial_narrows() -> None:
    short = make(4, "DATE", "PARTIAL", {"dates": ["2026-11-10"], "from": "13:00", "to": "20:00"})
    window = windows([short], [TUE])[(MUSEUM.place_id, TUE)]
    assert window.intervals == ((780, 1020),)


def test_partial_without_time_is_a_notice() -> None:
    partial = make(5, "SEASON", "PARTIAL", {"from_month_day": "09-01", "to_month_day": "12-31"})
    window = windows([partial], [TUE])[(MUSEUM.place_id, TUE)]
    assert window.intervals == ((480, 1020),)
    assert [n.conflict_type for n in window.notices] == ["SEASONAL_WARNING"]


def test_event_notice_and_ticket_attach_warnings() -> None:
    lantern = make(
        6,
        "LUNAR_DATE",
        "EVENT",
        {"lunar_days": [14], "from": "18:00", "to": "22:00", "restricted_modes": ["DRIVE"]},
        applies_to="AREA",
        place_id=None,
        area_code="hoi-an-old-town",
    )
    ticket = make(
        7,
        "TICKET_VALIDITY",
        "NOTICE",
        {"valid_same_day": True},
        applies_to="AREA",
        place_id=None,
        area_code="hoi-an-old-town",
    )
    window = windows([ticket, lantern], [LANTERN], [OLD_HOUSE])[(OLD_HOUSE.place_id, LANTERN)]
    assert window.intervals == ((480, 1020),)
    assert [(n.rule_id, n.conflict_type) for n in window.notices] == [
        (lantern.id, "LUNAR_EVENT_CONFLICT"),
        (ticket.id, "TICKET_VALIDITY"),
    ]
    assert window.notices[0].interval == (1080, 1320)
    assert window.notices[1].ticket_valid_same_day is True
    assert window.mode_restrictions[0].modes == frozenset({"DRIVE"})
    # The museum is in another area: untouched.
    other = windows([ticket, lantern], [LANTERN])[(MUSEUM.place_id, LANTERN)]
    assert other.notices == () and other.mode_restrictions == ()


def test_unknown_hours_stay_unknown_with_scheduling_default() -> None:
    result = windows([], [MON], [NO_HOURS])[(NO_HOURS.place_id, MON)]
    assert result.unknown_hours
    assert result.intervals == (DEFAULT_UNKNOWN_HOURS_WINDOW,)
    custom = effective_windows(
        base_hours={},
        rules=[],
        places=[NO_HOURS],
        dates=[MON],
        unknown_hours_window=(540, 960),
    )[(NO_HOURS.place_id, MON)]
    assert custom.unknown_hours and custom.intervals == ((540, 960),)


def test_draft_and_retired_rules_are_ignored() -> None:
    draft = make(8, "WEEKLY", "CLOSED", {"weekdays": [1]}, review_state="DRAFT")
    retired = make(9, "WEEKLY", "CLOSED", {"weekdays": [1]}, review_state="RETIRED")
    assert not windows([draft, retired], [MON])[(MUSEUM.place_id, MON)].is_closed


def test_regular_weekly_closure_from_hours() -> None:
    hours = OpeningHours.from_value(
        {"weekly": {"tue": [["08:00", "17:00"]], "3": [["07:30", "11:00"], ["13:00", "17:00"]]}}
    )
    result = effective_windows(
        base_hours={MUSEUM.place_id: hours}, rules=[], places=[MUSEUM], dates=[MON, TUE]
    )
    assert result[(MUSEUM.place_id, MON)].is_closed
    assert result[(MUSEUM.place_id, MON)].closed_rule_ids == ()
    assert result[(MUSEUM.place_id, TUE)].intervals == ((480, 1020),)
    assert hours.on(date(2026, 11, 11)) == ((450, 660), (780, 1020))


def test_overnight_hours_clamped_to_midnight() -> None:
    hours = OpeningHours.from_value({"6": [["17:00", "02:00"]]})
    assert hours.on(date(2026, 11, 14)) == ((1020, 1440),)


def test_rule_targets() -> None:
    area_rule = make(
        10,
        "WEEKLY",
        "NOTICE",
        {"weekdays": [1]},
        applies_to="AREA",
        place_id=None,
        area_code="hai-chau",
    )
    assert rule_targets(area_rule, MUSEUM)
    assert not rule_targets(area_rule, OLD_HOUSE)
    assert not rule_targets(area_rule, PlaceRef(MUSEUM.place_id, "hai-chau", OTHER_CITY))
    city_rule = make(11, "WEEKLY", "NOTICE", {"weekdays": [1]}, applies_to="CITY", place_id=None)
    assert rule_targets(city_rule, OLD_HOUSE)
    assert not rule_targets(city_rule, PlaceRef(uuid.UUID(int=5), None, OTHER_CITY))


def test_deterministic_and_validated() -> None:
    rules = [
        make(13, "WEEKLY", "NOTICE", {"weekdays": [1]}),
        make(12, "WEEKLY", "EVENT", {"weekdays": [1]}),
    ]
    first = windows(rules, [MON])
    second = windows(list(reversed(rules)), [MON])
    assert first == second
    assert [n.rule_id for n in first[(MUSEUM.place_id, MON)].notices] == [
        uuid.UUID(int=12),
        uuid.UUID(int=13),
    ]
    with pytest.raises(ValueError):
        effective_windows(base_hours={}, rules=[], places=[MUSEUM], dates=[MON], tz="Asia/Tokyo")
    with pytest.raises(ValueError):
        effective_windows(
            base_hours={}, rules=[], places=[MUSEUM], dates=[MON], unknown_hours_window=(600, 600)
        )

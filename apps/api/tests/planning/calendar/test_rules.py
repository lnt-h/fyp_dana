"""Closure rule parsing and occurrence for every rule kind (FR-102)."""

import uuid
from datetime import date, datetime
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from app.planning.calendar.rules import (
    ClosureRule,
    DateParams,
    WeeklyParams,
    hhmm_to_minutes,
    occurs_on,
)

PLACE = uuid.UUID("00000000-0000-0000-0000-00000000000a")
CITY = uuid.UUID("00000000-0000-0000-0000-0000000000c1")


def rule(kind: str, params: dict[str, Any], **extra: Any) -> ClosureRule:
    data: dict[str, Any] = {
        "id": uuid.UUID(int=1),
        "applies_to": "PLACE",
        "place_id": PLACE,
        "city_id": CITY,
        "rule_kind": kind,
        "effect": "CLOSED",
        "severity": "BLOCKING",
        "params": params,
    }
    data.update(extra)
    return ClosureRule.from_mapping(data)


def test_weekly() -> None:
    monday_closed = rule("WEEKLY", {"weekdays": [1]})
    assert isinstance(monday_closed.params, WeeklyParams)
    assert occurs_on(monday_closed, date(2026, 11, 9))  # Monday
    assert not occurs_on(monday_closed, date(2026, 11, 10))


def test_date_fixed_and_yearly() -> None:
    fixed = rule("DATE", {"dates": ["2026-09-02"]})
    assert isinstance(fixed.params, DateParams)
    assert occurs_on(fixed, date(2026, 9, 2))
    assert not occurs_on(fixed, date(2027, 9, 2))
    yearly = rule("DATE", {"month_day": ["04-30", "05-01"]})
    assert occurs_on(yearly, date(2027, 4, 30))
    assert occurs_on(yearly, date(2028, 5, 1))
    assert not occurs_on(yearly, date(2028, 5, 2))
    leap_day = rule("DATE", {"month_day": ["02-29"]})
    assert occurs_on(leap_day, date(2028, 2, 29))
    assert not occurs_on(leap_day, date(2027, 3, 1))


def test_lunar_date_tet_and_lantern_nights() -> None:
    tet = rule("LUNAR_DATE", {"lunar_days": [1, 2, 3], "lunar_months": [1]})
    assert occurs_on(tet, date(2026, 2, 17))
    assert occurs_on(tet, date(2026, 2, 19))
    assert not occurs_on(tet, date(2026, 2, 20))
    assert occurs_on(tet, date(2027, 2, 6))
    assert not occurs_on(tet, date(2026, 3, 19))  # lunar 2/2
    lantern = rule("LUNAR_DATE", {"lunar_days": [14]}, effect="EVENT", severity="WARNING")
    assert occurs_on(lantern, date(2026, 3, 2))
    assert occurs_on(lantern, date(2027, 9, 14))
    assert not occurs_on(lantern, date(2026, 3, 3))


def test_lunar_leap_month_matches_only_without_month_filter() -> None:
    # 2025-08-07 is lunar 14 of the leap 6th month.
    every_month = rule("LUNAR_DATE", {"lunar_days": [14]})
    sixth = rule("LUNAR_DATE", {"lunar_days": [14], "lunar_months": [6]})
    assert occurs_on(every_month, date(2025, 8, 7))
    assert not occurs_on(sixth, date(2025, 8, 7))
    assert occurs_on(sixth, date(2025, 7, 8))  # regular 6th month


def test_season_plain_and_wrapping() -> None:
    rainy = rule("SEASON", {"from_month_day": "09-01", "to_month_day": "12-31"}, effect="NOTICE")
    assert occurs_on(rainy, date(2026, 10, 15))
    assert not occurs_on(rainy, date(2026, 8, 31))
    winter = rule("SEASON", {"from_month_day": "12-15", "to_month_day": "02-15"}, effect="NOTICE")
    assert occurs_on(winter, date(2026, 12, 31))
    assert occurs_on(winter, date(2027, 1, 1))
    assert occurs_on(winter, date(2027, 2, 15))
    assert not occurs_on(winter, date(2027, 2, 16))


def test_ticket_validity_occurs_every_day_in_effect() -> None:
    ticket = rule(
        "TICKET_VALIDITY",
        {"valid_same_day": True},
        applies_to="AREA",
        place_id=None,
        area_code="hoi-an-old-town",
        effect="NOTICE",
        effective_from="2026-01-01",
    )
    assert occurs_on(ticket, date(2026, 6, 1))
    assert not occurs_on(ticket, date(2025, 12, 31))


def test_effective_range_is_inclusive() -> None:
    bounded = rule(
        "WEEKLY",
        {"weekdays": [1, 2, 3, 4, 5, 6, 7]},
        effective_from=date(2026, 12, 1),
        effective_to=date(2026, 12, 3),
    )
    assert not occurs_on(bounded, date(2026, 11, 30))
    assert occurs_on(bounded, date(2026, 12, 1))
    assert occurs_on(bounded, date(2026, 12, 3))
    assert not occurs_on(bounded, date(2026, 12, 4))


def test_optional_window_and_restricted_modes() -> None:
    partial = rule(
        "WEEKLY",
        {"weekdays": [6], "from": "08:00", "to": "12:00", "restricted_modes": ["DRIVE"]},
        effect="PARTIAL",
    )
    assert partial.interval == (480, 720)
    assert partial.restricted_modes == ("DRIVE",)
    assert hhmm_to_minutes("24:00") == 1440


@pytest.mark.parametrize(
    ("kind", "params"),
    [
        ("WEEKLY", {"weekdays": [0]}),
        ("WEEKLY", {"weekdays": [1], "from": "08:00"}),
        ("WEEKLY", {"weekdays": [1], "from": "12:00", "to": "08:00"}),
        ("DATE", {}),
        ("DATE", {"dates": ["2026-01-01"], "month_day": ["01-01"]}),
        ("DATE", {"month_day": ["13-01"]}),
        ("LUNAR_DATE", {"lunar_days": [31]}),
        ("LUNAR_DATE", {"lunar_days": [1], "lunar_months": [13]}),
        ("SEASON", {"from_month_day": "9-1", "to_month_day": "12-31"}),
        ("TICKET_VALIDITY", {}),
        ("TICKET_VALIDITY", {"valid_same_day": True, "valid_hours": 24}),
        ("WEEKLY", {"weekdays": [1], "restricted_modes": ["BIKE"]}),
    ],
)
def test_invalid_params_rejected(kind: str, params: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        rule(kind, params)


def test_invalid_targets_rejected() -> None:
    with pytest.raises(ValidationError):
        rule("WEEKLY", {"weekdays": [1]}, place_id=None)
    with pytest.raises(ValidationError):
        rule("WEEKLY", {"weekdays": [1]}, applies_to="AREA", place_id=None)
    with pytest.raises(ValidationError):
        rule(
            "WEEKLY",
            {"weekdays": [1]},
            effective_from=date(2026, 2, 1),
            effective_to=date(2026, 1, 1),
        )


def test_from_row_reads_orm_attributes() -> None:
    row = SimpleNamespace(
        id=uuid.UUID(int=7),
        city_id=CITY,
        applies_to="CITY",
        place_id=None,
        area_code=None,
        rule_kind="LUNAR_DATE",
        effect="CLOSED",
        severity="BLOCKING",
        params={"lunar_days": [1], "lunar_months": [1]},
        effective_from=None,
        effective_to=datetime(2030, 1, 1, 0, 0),
        review_state="DRAFT",
        note_vi="Tết",
        note_en="Tết",
    )
    parsed = ClosureRule.from_row(row)
    assert parsed.id == uuid.UUID(int=7)
    assert parsed.effective_to == date(2030, 1, 1)
    assert not parsed.is_active
    assert occurs_on(parsed, date(2026, 2, 17))


def test_unknown_param_keys_are_ignored() -> None:
    lenient = rule("WEEKLY", {"weekdays": [2], "curator_hint": "x"})
    assert occurs_on(lenient, date(2026, 11, 10))

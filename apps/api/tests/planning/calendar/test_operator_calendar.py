"""Every rule in the shipped operator calendars must parse on the planner side (DEC-016, DEC-022).

The calendar loader validates ``params`` with the curator validators; Plan Health re-parses the
stored row with :class:`ClosureRule`. If the two disagree, ``load_rules`` drops the rule with a
warning and the plan silently loses a calendar rule (2026-11-08: ``restricted_modes: TWO_WHEELER``).
"""

from __future__ import annotations

import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from app.ingestion.calendar import CALENDAR_DIR, RuleSpec, parse_rules
from app.planning.calendar.rules import ClosureRule, describe_rule_error

CALENDARS = sorted(CALENDAR_DIR.glob("*.yaml"))


def _rule_from_spec(spec: RuleSpec) -> ClosureRule:
    """Mirror a stored ``place_closure_rules`` row and parse it through ``ClosureRule.from_row``."""
    row = SimpleNamespace(
        id=uuid.uuid4(),
        city_id=uuid.uuid4(),
        applies_to=spec.applies_to,
        place_id=uuid.uuid4() if spec.applies_to == "PLACE" else None,
        area_code=spec.area_code,
        rule_kind=spec.rule_kind,
        effect=spec.effect,
        severity=spec.severity,
        params=spec.params,
        effective_from=spec.effective_from,
        effective_to=spec.effective_to,
        review_state="APPROVED",
    )
    return ClosureRule.from_row(row)


def test_da_nang_calendar_is_shipped() -> None:
    assert CALENDAR_DIR / "da-nang.yaml" in CALENDARS


@pytest.mark.parametrize("path", CALENDARS, ids=lambda p: Path(p).name)
def test_every_calendar_rule_parses_for_planning(path: Path) -> None:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    specs = parse_rules(document)
    assert len(specs) == len(document["rules"])
    failures: list[str] = []
    parsed: list[ClosureRule] = []
    for index, spec in enumerate(specs, start=1):
        try:
            parsed.append(_rule_from_spec(spec))
        except ValueError as exc:
            failures.append(f"rule {index}: {describe_rule_error(exc)}")
    assert failures == []
    assert len(parsed) == len(specs)
    assert all(rule.is_active for rule in parsed)


def test_hoi_an_walking_hours_keeps_two_wheeler_restriction() -> None:
    rule = ClosureRule.from_mapping(
        {
            "id": uuid.uuid4(),
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
    assert rule.restricted_modes == ("DRIVE", "TWO_WHEELER")
    assert rule.interval == (15 * 60, 22 * 60)


def test_parse_error_reason_names_the_field_not_the_value() -> None:
    secret = "SECRET-MODE-VALUE"
    with pytest.raises(ValueError) as caught:
        ClosureRule.from_mapping(
            {
                "id": uuid.uuid4(),
                "applies_to": "CITY",
                "city_id": uuid.uuid4(),
                "rule_kind": "WEEKLY",
                "effect": "NOTICE",
                "params": {"weekdays": [1], "restricted_modes": [secret]},
            }
        )
    reason = describe_rule_error(caught.value)
    assert "restricted_modes" in reason
    assert secret not in reason

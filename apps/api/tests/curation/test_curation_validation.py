"""Pure validation rules of the curation package (no database)."""

from typing import Any

import pytest
from pydantic import ValidationError

from app.curation.chunks import chunk_index, content_sha256
from app.curation.closure_rules import default_severity, validate_params
from app.curation.common import (
    decode_cursor,
    encode_cursor,
    normalize_search_text,
    parse_point,
    slugify,
    to_ewkt,
)
from app.curation.facts import validate_conflict, validate_fact_value
from app.errors import AppError
from app.models.reference import FactField
from app.schemas.admin import (
    CandidateReview,
    ChunkInput,
    GeoPoint,
    LocalizationInput,
    WebCandidateReview,
)


@pytest.mark.parametrize(
    ("kind", "params", "expected"),
    [
        ("WEEKLY", {"weekdays": [1]}, {"weekdays": [1]}),
        (
            "WEEKLY",
            {"weekdays": [6, 7], "from": "12:00", "to": "14:00"},
            {"weekdays": [6, 7], "from": "12:00", "to": "14:00"},
        ),
        ("DATE", {"dates": ["2027-02-06"]}, {"dates": ["2027-02-06"]}),
        ("DATE", {"month_day": ["09-02"]}, {"month_day": ["09-02"]}),
        ("LUNAR_DATE", {"lunar_days": [14]}, {"lunar_days": [14]}),
        (
            "SEASON",
            {"from_month_day": "09-01", "to_month_day": "12-31"},
            {"from_month_day": "09-01", "to_month_day": "12-31"},
        ),
        ("TICKET_VALIDITY", {"valid_same_day": True}, {"valid_same_day": True}),
        ("TICKET_VALIDITY", {"valid_hours": 24}, {"valid_hours": 24}),
    ],
)
def test_valid_rule_params(kind: str, params: dict[str, Any], expected: dict[str, Any]) -> None:
    assert validate_params(kind, params) == expected


@pytest.mark.parametrize(
    ("kind", "params"),
    [
        ("WEEKLY", {}),
        ("WEEKLY", {"weekdays": [0]}),
        ("WEEKLY", {"weekdays": [1, 1]}),
        ("WEEKLY", {"weekdays": [1], "from": "12:00"}),
        ("WEEKLY", {"weekdays": [1], "extra": True}),
        ("DATE", {}),
        ("DATE", {"dates": ["2027-02-06"], "month_day": ["01-01"]}),
        ("DATE", {"month_day": ["13-01"]}),
        ("LUNAR_DATE", {"lunar_days": [31]}),
        ("LUNAR_DATE", {"lunar_days": [1], "lunar_months": [13]}),
        ("SEASON", {"from_month_day": "9-1", "to_month_day": "12-31"}),
        ("TICKET_VALIDITY", {}),
        ("TICKET_VALIDITY", {"valid_same_day": True, "valid_hours": 3}),
        ("TICKET_VALIDITY", {"valid_hours": 0}),
    ],
)
def test_invalid_rule_params(kind: str, params: dict[str, Any]) -> None:
    with pytest.raises(AppError) as caught:
        validate_params(kind, params)
    assert caught.value.status_code == 422
    assert caught.value.code == "invalid_rule_params"
    assert caught.value.context["fields"]


def test_default_severity() -> None:
    assert default_severity("CLOSED") == "BLOCKING"
    assert default_severity("EVENT") == "WARNING"


def test_search_normalisation_and_slug() -> None:
    assert normalize_search_text("  Đà   Nẵng ") == "da nang"
    assert normalize_search_text("Chùa Cầu Hội An") == "chua cau hoi an"
    assert slugify("Chùa Cầu (Hội An)!") == "chua-cau-hoi-an"
    assert slugify("!!!") == "place"


def test_cursor_round_trip_and_rejection() -> None:
    assert decode_cursor(None) == 0
    assert decode_cursor(encode_cursor(40)) == 40
    for bad in ("not-a-cursor", encode_cursor(-1)):
        with pytest.raises(AppError) as caught:
            decode_cursor(bad)
        assert caught.value.status_code == 400
        assert caught.value.code == "invalid_cursor"


def test_point_round_trip() -> None:
    point = GeoPoint(latitude=16.0544, longitude=108.2208)
    assert to_ewkt(point) == "SRID=4326;POINT(108.2208 16.0544)"
    assert parse_point(to_ewkt(point)) == point
    assert parse_point(None) is None


def test_fact_value_rules() -> None:
    location = FactField(code="ENTRANCE_LOCATION", value_kind="LOCATION", is_operational=True)
    text_field = FactField(code="ADDRESS_VI", value_kind="TEXT", is_operational=True)
    validate_fact_value(location, "KNOWN", {"lat": 16.0, "lng": 108.2})
    validate_fact_value(text_field, "UNKNOWN", None)
    cases: list[tuple[FactField, str, dict[str, Any] | None, str]] = [
        (text_field, "KNOWN", None, "fact_value_required"),
        (text_field, "UNKNOWN", {"text": "x"}, "fact_value_forbidden"),
        (location, "KNOWN", {"lat": 95, "lng": 108}, "fact_value_invalid"),
        (location, "KNOWN", {"lat": "16", "lng": 108}, "fact_value_invalid"),
    ]
    for field, state, value, code in cases:
        with pytest.raises(AppError) as caught:
            validate_fact_value(field, state, value)
        assert caught.value.code == code
    with pytest.raises(AppError):
        validate_conflict("OPEN", None)
    validate_conflict("NONE", None)


def test_schema_rules() -> None:
    with pytest.raises(ValidationError):
        LocalizationInput(locale="vi")
    with pytest.raises(ValidationError):
        WebCandidateReview(decision="REJECT")
    with pytest.raises(ValidationError):
        CandidateReview.model_validate({"expected_content_revision": 1, "facts": []})
    with pytest.raises(ValidationError):
        ChunkInput.model_validate(
            {"locale": "vi", "section": "CITY_OVERVIEW", "content": "x", "source_revision_ids": []}
        )
    review = CandidateReview.model_validate({"expected_content_revision": 3, "area_code": None})
    assert "area_code" in review.model_fields_set


def test_chunk_helpers() -> None:
    assert chunk_index("OVERVIEW") == 0
    assert chunk_index("ACCESS") == 5
    assert len(content_sha256("xin chào")) == 64

"""Pure pipeline rules: areas, sheet parsing, calendar validation, composition and the gate."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yaml

from app.curation.auto_publish import Contributions, SourceInfo, compose, gate_reasons
from app.ingestion.areas import (
    AREAS_DIR,
    assign_area,
    hoi_an_area_codes,
    load_areas,
    parse_areas,
    point_in_ring,
)
from app.ingestion.calendar import CALENDAR_DIR, parse_rules
from app.ingestion.common import PROVENANCE_KEY
from app.ingestion.sheet import parse_opening_hours, parse_rows
from app.models.catalog import Place
from app.models.reference import FactField

AREAS = load_areas("da-nang")

HEADER = (
    "slug,category_code,area_code,lat,lng,name_vi,name_en,short_description_vi,"
    "short_description_en,source_url,source_publisher,licence,opening_hours,"
    "opening_hours_source_url,entrance_lat,entrance_lng,entrance_source_url\n"
)


def test_point_in_ring_square() -> None:
    ring = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0))
    assert point_in_ring(0.5, 0.5, ring)
    assert point_in_ring(1.0, 0.5, ring)  # on an edge
    assert not point_in_ring(1.5, 0.5, ring)


@pytest.mark.parametrize(
    ("name", "lng", "lat", "area"),
    [
        ("Japanese Covered Bridge", 108.3262, 15.8771, "hoi-an-old-town"),
        ("Thanh Hà pottery village", 108.3036, 15.8808, "hoi-an-old-town"),
        ("Trà Quế vegetable village", 108.3286, 15.9016, "hoi-an-old-town"),
        ("An Bàng beach", 108.3415, 15.9135, "hoi-an-beaches-islands"),
        ("Cửa Đại beach", 108.3670, 15.8890, "hoi-an-beaches-islands"),
        ("Cù Lao Chàm", 108.5100, 15.9500, "hoi-an-beaches-islands"),
        ("Linh Ứng pagoda (Sơn Trà)", 108.2779, 16.1003, "son-tra"),
        ("Marble Mountains", 108.2638, 16.0036, "my-khe-ngu-hanh-son"),
        ("My Khe beach", 108.2470, 16.0600, "my-khe-ngu-hanh-son"),
        ("Museum of Cham Sculpture", 108.2236, 16.0606, "da-nang-center"),
        ("Bà Nà Hills", 107.9960, 15.9950, "ba-na-hoa-vang"),
        ("Hải Vân pass", 108.1300, 16.1970, "ba-na-hoa-vang"),
        ("Bạch Mã national park (Huế)", 107.8500, 16.1900, None),
        # 2026-11-08 polygons: real clusters that were outside every area.
        ("Mỹ Sơn sanctuary", 108.1240, 15.7640, "my-son"),
        ("Quảng Nam citadel (Thanh Chiêm)", 108.2546, 15.8885, "hoi-an-outskirts"),
        ("Gò Nổi bridge", 108.2626, 15.8513, "hoi-an-outskirts"),
        ("Nam Phước market", 108.2808, 15.8434, "hoi-an-outskirts"),
        ("Cham Islands (Wikidata point)", 108.6800, 15.9500, "hoi-an-beaches-islands"),
        ("Hàn river bridge", 108.2267, 16.0723, "da-nang-center"),
        ("Thuận Phước bridge", 108.2220, 16.0919, "da-nang-center"),
        ("An Hải Bắc market (east bank)", 108.2315, 16.0809, "my-khe-ngu-hanh-son"),
        ("Vincom Plaza (east bank)", 108.2303, 16.0714, "my-khe-ngu-hanh-son"),
        ("Quảng Nam museum (Tam Kỳ)", 108.4756, 15.5799, "tam-ky"),
        # Still outside: no catch-all area.
        ("Bằng An tower (Điện Bàn)", 108.2327, 15.8845, None),
        ("Lăng Cô beach (Huế)", 108.0600, 16.2700, None),
        ("Sơn Mỹ memorial (Quảng Ngãi)", 108.8900, 15.1800, None),
        ("Ngọc Linh mountain", 107.9800, 15.0700, None),
    ],
)
def test_area_assignment_of_landmarks(name: str, lng: float, lat: float, area: str | None) -> None:
    assert assign_area(AREAS, lng, lat) == area, name


def test_area_file_matches_the_seeded_codes_and_names() -> None:
    from app.cli import AREAS as SEEDED

    document = yaml.safe_load((AREAS_DIR / "da-nang.yaml").read_text(encoding="utf-8"))
    areas = parse_areas(document)
    assert sorted(area.code for area in areas) == sorted(code for code, _, _ in SEEDED)
    seeded = {code: (vi, en) for code, vi, en in SEEDED}
    for area in areas:
        assert (area.name_vi, area.name_en) == seeded[area.code], area.code
    assert hoi_an_area_codes(areas) == {
        "hoi-an-old-town",
        "hoi-an-beaches-islands",
        "hoi-an-outskirts",
    }
    with pytest.raises(ValueError):
        parse_areas({"areas": [{"code": "x", "polygon": [[0, 0], [1, 1]]}]})


def test_opening_hours_shape() -> None:
    assert parse_opening_hours("mon-fri 08:00-11:30,13:30-17:00; sat closed") == {
        "1": [["08:00", "11:30"], ["13:30", "17:00"]],
        "2": [["08:00", "11:30"], ["13:30", "17:00"]],
        "3": [["08:00", "11:30"], ["13:30", "17:00"]],
        "4": [["08:00", "11:30"], ["13:30", "17:00"]],
        "5": [["08:00", "11:30"], ["13:30", "17:00"]],
        "6": [],
    }
    assert set(parse_opening_hours("daily 07:00-24:00")) == {str(d) for d in range(1, 8)}
    for bad in (
        "",
        "someday 08:00-09:00",
        "mon 09:00-08:00",
        "mon 8-9",
        "mon 08:00-09:00; mon closed",
    ):
        with pytest.raises(ValueError):
            parse_opening_hours(bad)


def test_sheet_rows_validate() -> None:
    text = HEADER + (
        "chua-cau,heritage,,15.8771,108.3262,Chùa Cầu,Japanese Covered Bridge,Cầu cổ,Old bridge,"
        "https://hoianworldheritage.org.vn/,Hội An Center for Cultural Heritage,CC-BY-4.0,"
        "daily 08:00-21:00,https://hoianworldheritage.org.vn/hours,,,\n"
        "Bad Slug,HERITAGE,,15.8,108.3,A,B,,,https://x.test/,X,CC0,,,,,\n"
        "no-source,HERITAGE,,15.8,108.3,A,B,,,,,,,,,,\n"
        "fact-no-source,HERITAGE,,15.8,108.3,A,B,,,https://x.test/,X,CC0,daily 08:00-09:00,,,,\n"
        "no-licence,BEACH,,15.91,108.34,A,B,,,https://x.test/,X,,,,,,\n"
    )
    rows, errors = parse_rows(text)
    assert [row.slug for row in rows] == ["chua-cau", "no-licence"]
    assert {error.reason for error in errors} == {
        "INVALID_SLUG",
        "NO_SOURCE",
        "FACT_WITHOUT_SOURCE:OPENING_HOURS",
    }
    bridge = rows[0]
    assert bridge.category_code == "HERITAGE"
    assert bridge.facts[0].field_code == "OPENING_HOURS"
    assert bridge.facts[0].value["weekly"]["1"] == [["08:00", "21:00"]]
    assert rows[1].licence == "UNKNOWN" and rows[1].attribution is None
    with pytest.raises(ValueError):
        parse_rows("slug,lat\nx,1\n")


def test_operator_calendar_file_is_valid() -> None:
    document = yaml.safe_load((CALENDAR_DIR / "da-nang.yaml").read_text(encoding="utf-8"))
    rules = parse_rules(document)
    kinds = {rule.rule_kind for rule in rules}
    assert {"DATE", "LUNAR_DATE", "TICKET_VALIDITY", "WEEKLY"} <= kinds
    lantern = [r for r in rules if r.rule_kind == "LUNAR_DATE" and r.area_code == "hoi-an-old-town"]
    assert lantern and lantern[0].effect == "EVENT" and lantern[0].params == {"lunar_days": [14]}
    car_free = [r for r in rules if r.params.get("restricted_modes")]
    assert car_free and car_free[0].params["restricted_modes"] == ["DRIVE", "TWO_WHEELER"]


@pytest.mark.parametrize(
    "rule",
    [
        {
            "applies_to": "AREA",
            "rule_kind": "WEEKLY",
            "effect": "CLOSED",
            "params": {"weekdays": [1]},
            "note_vi": "x",
            "note_en": "x",
        },
        {
            "applies_to": "CITY",
            "rule_kind": "MONTHLY",
            "effect": "CLOSED",
            "params": {},
            "note_vi": "x",
            "note_en": "x",
        },
        {
            "applies_to": "CITY",
            "rule_kind": "WEEKLY",
            "effect": "CLOSED",
            "params": {"weekdays": [9]},
            "note_vi": "x",
            "note_en": "x",
        },
        {
            "applies_to": "CITY",
            "rule_kind": "WEEKLY",
            "effect": "CLOSED",
            "params": {"weekdays": [1]},
            "note_vi": "",
            "note_en": "x",
        },
    ],
)
def test_invalid_calendar_rules(rule: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        parse_rules({"rules": [rule]})


def _fields() -> list[FactField]:
    return [
        FactField(code="ADDRESS_VI", required_for_publication=True, is_operational=True),
        FactField(code="OPENING_HOURS", required_for_publication=True, is_operational=True),
        FactField(code="DRESS_CODE", required_for_publication=False, is_operational=True),
    ]


def _place(lng: float, lat: float) -> Place:
    return Place(
        id=uuid.uuid4(), slug="p", location=f"SRID=4326;POINT({lng} {lat})", category_code=None
    )


def test_compose_and_gate_pass_for_bilingual_wikidata_place() -> None:
    wd_rev, vi_rev, en_rev = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    contributions = Contributions(
        wikidata={
            "name": {"vi": "Chùa Cầu", "en": "Japanese Covered Bridge"},
            "location": {"lat": 15.8771, "lng": 108.3262},
            "category": "HERITAGE",
            "description": {"vi": "cầu cổ", "en": "covered bridge"},
            "aliases": {"vi": ["Lai Viễn Kiều"]},
            PROVENANCE_KEY: {"source_revision_id": str(wd_rev)},
        },
        wikipedia={
            "vi": {
                "summary": "Chùa Cầu là ...",
                PROVENANCE_KEY: {"source_revision_id": str(vi_rev)},
            },
            "en": {
                "summary": "The bridge ...",
                PROVENANCE_KEY: {"source_revision_id": str(en_rev)},
            },
        },
    )
    desired = compose(
        _place(108.0, 16.0),
        contributions,
        area_codes=AREAS,
        categories={"HERITAGE"},
        fact_fields=_fields(),
    )
    assert desired.area_code == "hoi-an-old-town"
    assert desired.visit_minutes == (30, 60, 120)
    assert desired.localizations["vi"].description == "Chùa Cầu là ..."
    assert desired.localizations["en"].short_description == "covered bridge"
    assert desired.aliases["vi"] == ["Chùa Cầu", "Lai Viễn Kiều"]
    assert [(f.field_code, f.knowledge_state) for f in desired.facts] == [
        ("ADDRESS_VI", "UNKNOWN"),
        ("OPENING_HOURS", "UNKNOWN"),
    ]  # never invented; optional fields without a source are omitted
    assert all(f.evidence[0][0] == wd_rev for f in desired.facts)
    assert {c.locale for c in desired.chunks} == {"vi", "en"}
    sources = {
        wd_rev: SourceInfo("Wikidata", "CC0-1.0", "Wikidata (CC0)"),
        vi_rev: SourceInfo("Wikipedia (vi)", "CC-BY-SA-4.0", "Wikipedia contributors"),
        en_rev: SourceInfo("Wikipedia (en)", "CC-BY-SA-4.0", "Wikipedia contributors"),
    }
    assert gate_reasons(desired, inside=True, sources=sources) == []
    assert gate_reasons(desired, inside=False, sources=sources) == ["OUTSIDE_CITY"]
    unlicensed = {**sources, vi_rev: SourceInfo("Wikipedia (vi)", "UNKNOWN", None)}
    assert gate_reasons(desired, inside=True, sources=unlicensed) == [
        "MISSING_LICENCE:Wikipedia (vi)"
    ]


def test_gate_rejects_missing_locale_and_area() -> None:
    rev = uuid.uuid4()
    contributions = Contributions(
        wikidata={
            "name": {"vi": "Núi Chúa"},
            "location": {"lat": 15.70, "lng": 107.90},
            "category": "NATURE",
            PROVENANCE_KEY: {"source_revision_id": str(rev)},
        }
    )
    desired = compose(
        _place(107.9, 15.7),
        contributions,
        area_codes=AREAS,
        categories={"NATURE"},
        fact_fields=_fields(),
    )
    reasons = gate_reasons(
        desired, inside=True, sources={rev: SourceInfo("Wikidata", "CC0-1.0", "Wikidata (CC0)")}
    )
    assert reasons == [
        "MISSING_AREA",
        "MISSING_DESCRIPTION:vi",
        "MISSING_NAME:en",
        "MISSING_DESCRIPTION:en",
    ]


def test_gate_requires_a_source() -> None:
    desired = compose(
        _place(108.3262, 15.8771),
        Contributions(),
        area_codes=AREAS,
        categories=set(),
        fact_fields=_fields(),
    )
    assert "NO_SOURCE" in gate_reasons(desired, inside=True, sources={})


def test_calendar_dir_exists() -> None:
    assert Path(CALENDAR_DIR, "da-nang.yaml").exists()

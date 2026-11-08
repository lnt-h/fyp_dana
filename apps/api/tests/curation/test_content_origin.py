"""EN proper-name fallback and AI-summary descriptions in composition and the gate (D3)."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.curation.auto_publish import Contributions, SourceInfo, compose, gate_reasons
from app.curation.names import proper_name_fallback
from app.ingestion.areas import load_areas
from app.ingestion.common import PROVENANCE_KEY
from app.models.catalog import Place

AREAS = load_areas("da-nang")
CATEGORIES = {"FOOD", "CAFE", "MARKET", "RELIGIOUS_SITE", "CRAFT_VILLAGE", "NATURE", "HERITAGE"}
OSM = SourceInfo("OpenStreetMap", "ODbL-1.0", "© OpenStreetMap contributors")
SUMMARY = SourceInfo("Gonarra", "GONARRA-AI-SUMMARY", "Short description written by Gonarra")
WEB = SourceInfo("example.vn", "UNKNOWN", "example.vn")


@pytest.mark.parametrize(
    ("category", "name", "expected"),
    [
        ("FOOD", "Bánh mì Phượng", "Bánh mì Phượng"),
        ("CAFE", "Cộng Cà Phê", "Cộng Cà Phê"),
        ("MARKET", "Chợ Hàn", "Chợ Hàn"),
        ("RELIGIOUS_SITE", "Chùa Linh Ứng", "Chùa Linh Ứng"),
        ("CRAFT_VILLAGE", "Làng gốm Thanh Hà", "Làng gốm Thanh Hà"),
        ("NATURE", "Núi Sà Trúc", None),  # generic part ("Núi") would need a translation
        ("HERITAGE", "Bảo tàng Đà Nẵng", None),
        ("HERITAGE", "Mỹ Sơn E7", "Mỹ Sơn E7"),  # proper noun without a generic part
        ("FOOD", "  ", None),
        (None, "Hội An", None),
    ],
)
def test_proper_name_fallback(category: str | None, name: str, expected: str | None) -> None:
    assert proper_name_fallback(category, name) == expected


def _place() -> Place:
    return Place(
        id=uuid.uuid4(),
        slug="p",
        location="SRID=4326;POINT(108.3262 15.8771)",
        category_code=None,
    )


def _osm(rev: uuid.UUID, category: str, name: dict[str, str]) -> dict[str, Any]:
    return {
        "name": name,
        "location": {"lat": 15.8771, "lng": 108.3262},
        "category": category,
        PROVENANCE_KEY: {"source_revision_id": str(rev)},
    }


def _summary(rev: uuid.UUID, cited: list[uuid.UUID]) -> dict[str, Any]:
    return {
        "description": {"vi": "Mô tả tiếng Việt. Câu thứ hai.", "en": "English text. Second."},
        "cited_urls": ["https://example.vn/x"],
        PROVENANCE_KEY: {
            "source_revision_id": str(rev),
            "cited_source_revision_ids": [str(r) for r in cited],
        },
    }


def test_compose_uses_vi_proper_name_and_ai_summary() -> None:
    osm_rev, summary_rev, cited_rev = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    contributions = Contributions(
        osm=_osm(osm_rev, "CAFE", {"vi": "Cộng Cà Phê"}),
        ai_summary=_summary(summary_rev, [cited_rev]),
    )
    desired = compose(
        _place(), contributions, area_codes=AREAS, categories=CATEGORIES, fact_fields=()
    )
    vi, en = desired.localizations["vi"], desired.localizations["en"]
    assert (vi.name, vi.name_is_source_fallback) == ("Cộng Cà Phê", False)
    assert (en.name, en.name_is_source_fallback) == ("Cộng Cà Phê", True)
    assert osm_rev in en.source_revision_ids
    assert vi.translation_origin == en.translation_origin == "AI_SUMMARY"
    assert en.description == "English text. Second."
    assert summary_rev in en.source_revision_ids and cited_rev not in en.source_revision_ids
    assert en.cited_revision_ids == {cited_rev}
    # Cited web pages are provenance, not shown content: their UNKNOWN licence is no blocker.
    sources = {osm_rev: OSM, summary_rev: SUMMARY, cited_rev: WEB}
    assert gate_reasons(desired, inside=True, sources=sources) == []
    # The cited revision must exist.
    missing = {osm_rev: OSM, summary_rev: SUMMARY}
    assert gate_reasons(desired, inside=True, sources=missing) == [
        "AI_SUMMARY_UNCITED:vi",
        "AI_SUMMARY_UNCITED:en",
    ]


def test_wikipedia_beats_ai_summary_per_locale() -> None:
    osm_rev, wiki_rev, summary_rev, cited_rev = (uuid.uuid4() for _ in range(4))
    contributions = Contributions(
        osm=_osm(osm_rev, "HERITAGE", {"vi": "Mỹ Sơn E7", "en": "My Son E7"}),
        wikipedia={
            "vi": {
                "summary": "Bài Wikipedia.",
                PROVENANCE_KEY: {"source_revision_id": str(wiki_rev)},
            }
        },
        ai_summary=_summary(summary_rev, [cited_rev]),
    )
    desired = compose(
        _place(), contributions, area_codes=AREAS, categories=CATEGORIES, fact_fields=()
    )
    assert desired.localizations["vi"].translation_origin == "ORIGINAL"
    assert desired.localizations["vi"].description == "Bài Wikipedia."
    assert desired.localizations["en"].translation_origin == "AI_SUMMARY"
    assert not desired.localizations["en"].name_is_source_fallback


def test_generic_name_gets_no_fallback() -> None:
    rev = uuid.uuid4()
    contributions = Contributions(osm=_osm(rev, "NATURE", {"vi": "Núi Sà Trúc"}))
    desired = compose(
        _place(), contributions, area_codes=AREAS, categories=CATEGORIES, fact_fields=()
    )
    assert desired.localizations["en"].name is None
    assert "MISSING_NAME:en" in gate_reasons(desired, inside=True, sources={rev: OSM})

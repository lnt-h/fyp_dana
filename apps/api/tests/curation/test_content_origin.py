"""EN proper-name fallback, retired AI summaries (DEC-031) and description sources."""

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


LONG_VI = "Mô tả tiếng Việt viết bởi con người, đủ dài để không bị coi là một dòng mô tả sơ sài."
LONG_EN = "A human-written English description that is long enough not to count as a stub line."


def test_ai_summary_is_retired_by_default() -> None:
    """DEC-031: staged AI summaries are ignored; the place keeps its names, no description."""
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
    assert vi.description is None and en.description is None
    assert vi.translation_origin == en.translation_origin == "ORIGINAL"
    reasons = gate_reasons(desired, inside=True, sources={osm_rev: OSM})
    # An OSM element alone is not a catalog place; no AI content and (option A) no
    # MISSING_DESCRIPTION.
    assert reasons == ["NO_EDITORIAL_SOURCE"]
    assert "MISSING_DESCRIPTION:vi" in gate_reasons(
        desired, inside=True, sources={osm_rev: OSM}, require_description=True
    )


def test_ai_summary_restore_path_needs_the_flag() -> None:
    osm_rev, summary_rev, cited_rev = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    summary = _summary(summary_rev, [cited_rev])
    summary["description"] = {"vi": LONG_VI, "en": LONG_EN}
    contributions = Contributions(
        osm=_osm(osm_rev, "CAFE", {"vi": "Cộng Cà Phê"}), ai_summary=summary
    )
    desired = compose(
        _place(),
        contributions,
        area_codes=AREAS,
        categories=CATEGORIES,
        fact_fields=(),
        allow_ai_content=True,
    )
    en = desired.localizations["en"]
    assert en.translation_origin == "AI_SUMMARY" and en.description == LONG_EN
    assert en.cited_revision_ids == {cited_rev}
    sources = {osm_rev: OSM, summary_rev: SUMMARY, cited_rev: WEB}
    assert "AI_CONTENT" not in gate_reasons(
        desired, inside=True, sources=sources, allow_ai_content=True
    )
    # The same composition without the flag is rejected by the AI_CONTENT rule.
    assert "AI_CONTENT" in gate_reasons(desired, inside=True, sources=sources)


def test_wikipedia_via_own_qid_and_stub_rule() -> None:
    osm_rev, wiki_rev, other_rev = (uuid.uuid4() for _ in range(3))
    contributions = Contributions(
        osm=_osm(osm_rev, "HERITAGE", {"vi": "Mỹ Sơn E7", "en": "My Son E7"}),
        wikipedia={
            "vi": {
                "summary": LONG_VI,
                "wikibase_item": "Q1",
                PROVENANCE_KEY: {"source_revision_id": str(wiki_rev)},
            },
            "en": {
                # The sitelink redirects to an article about another item (Réhahn case).
                "summary": LONG_EN,
                "wikibase_item": "Q2",
                PROVENANCE_KEY: {"source_revision_id": str(other_rev)},
            },
        },
        qid="Q1",
    )
    desired = compose(
        _place(), contributions, area_codes=AREAS, categories=CATEGORIES, fact_fields=()
    )
    assert desired.localizations["vi"].description == LONG_VI
    assert desired.localizations["vi"].description_source_revision_id == wiki_rev
    assert desired.localizations["en"].description is None
    assert "DESCRIPTION_OTHER_ENTITY:en" in desired.notes
    assert [c.section for c in desired.chunks] == ["OVERVIEW"]
    short = Contributions(
        osm=_osm(osm_rev, "HERITAGE", {"vi": "Mỹ Sơn E7", "en": "My Son E7"}),
        wikipedia={
            "vi": {
                "summary": "Cầu ở Việt Nam",
                PROVENANCE_KEY: {"source_revision_id": str(wiki_rev)},
            }
        },
        qid="Q1",
    )
    stub = compose(_place(), short, area_codes=AREAS, categories=CATEGORIES, fact_fields=())
    assert stub.localizations["vi"].description is None
    assert any(n.startswith("DESCRIPTION_TOO_SHORT:vi") for n in stub.notes)


def test_generic_name_gets_no_fallback() -> None:
    rev = uuid.uuid4()
    contributions = Contributions(osm=_osm(rev, "NATURE", {"vi": "Núi Sà Trúc"}))
    desired = compose(
        _place(), contributions, area_codes=AREAS, categories=CATEGORIES, fact_fields=()
    )
    assert desired.localizations["en"].name is None
    assert "MISSING_NAME:en" in gate_reasons(desired, inside=True, sources={rev: OSM})


def test_vi_name_without_diacritics_is_rejected() -> None:
    """Undiacriticized VI names ("Com Nieu Nha Do") hold for the owner sheet spelling."""
    rev = uuid.uuid4()
    contributions = Contributions(osm=_osm(rev, "HERITAGE", {"vi": "Com Nieu Nha Do"}))
    desired = compose(
        _place(), contributions, area_codes=AREAS, categories=CATEGORIES, fact_fields=()
    )
    assert "VI_NAME_NOT_VIETNAMESE" in gate_reasons(desired, inside=True, sources={rev: OSM})


def test_venue_brand_kept_but_descriptive_stall_is_not() -> None:
    rev = uuid.uuid4()
    brand = compose(
        _place(),
        Contributions(osm=_osm(rev, "FOOD", {"vi": "Morning Glory"})),
        area_codes=AREAS,
        categories=CATEGORIES,
        fact_fields=(),
    )
    assert "VI_NAME_NOT_VIETNAMESE" not in gate_reasons(brand, inside=True, sources={rev: OSM})
    stall = compose(
        _place(),
        Contributions(osm=_osm(rev, "FOOD", {"vi": "Banana fritters stall"})),
        area_codes=AREAS,
        categories=CATEGORIES,
        fact_fields=(),
    )
    reasons = gate_reasons(stall, inside=True, sources={rev: OSM})
    assert "VI_NAME_NOT_VIETNAMESE" in reasons  # owner supplies the curated name
    assert "NO_EDITORIAL_SOURCE" in reasons  # OSM alone never vouches a "... stall"


def test_swapped_vi_en_is_rejected() -> None:
    """"Thia Go" / "Thìa Gỗ": locales exchanged, owner fixes the order in the sheet."""
    rev = uuid.uuid4()
    contributions = Contributions(
        osm=_osm(rev, "FOOD", {"vi": "Thia Go", "en": "Thìa Gỗ"})
    )
    desired = compose(
        _place(), contributions, area_codes=AREAS, categories=CATEGORIES, fact_fields=()
    )
    assert "NAME_SWAPPED" in gate_reasons(desired, inside=True, sources={rev: OSM})

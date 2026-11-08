"""Enrichment priority (D3, 2026-11-08): tiers, Hội An first, FOOD + CAFE cap, limit."""

from __future__ import annotations

import uuid
from typing import Any

from app.agents.schemas import DescriptionSource
from app.curation.auto_publish import Contributions
from app.research.enrich import EnrichCandidate, needs_description, prioritise

WIKI = DescriptionSource(
    url="https://vi.wikipedia.org/wiki/X", title="X", text="x", kind="WIKIPEDIA"
)


def cand(slug: str, **overrides: Any) -> EnrichCandidate:
    base: dict[str, Any] = {
        "place_id": uuid.uuid4(),
        "slug": slug,
        "category": "HERITAGE",
        "area_code": "da-nang-center",
        "name_vi": slug,
        "name_en": None,
        "hoi_an": False,
        "wikidata": False,
        "osm_signal": False,
        "website": None,
        "has_hours": False,
    }
    base.update(overrides)
    return EnrichCandidate(**base)


def test_tiers() -> None:
    assert cand("a", wikidata=True).tier == 1
    assert cand("b", wikidata=True, area_code=None).tier is None  # outside every area
    assert cand("c", category="NATURE").tier == 2  # tourism category
    assert cand("d", category="NIGHTLIFE", osm_signal=True).tier == 2
    assert cand("e", category="NIGHTLIFE").tier is None
    # FOOD/CAFE/MARKET: website or hours AND (EN name or Hội An area).
    assert cand("f", category="FOOD", website="https://f.vn", name_en="F").tier == 3
    assert cand("g", category="CAFE", has_hours=True, hoi_an=True).tier == 3
    assert cand("h", category="CAFE", has_hours=True).tier is None
    assert cand("i", category="MARKET", name_en="I").tier is None
    assert cand("j", category="FOOD", wikidata=True, website="https://j.vn", hoi_an=True).tier == 3


def test_priority_order_and_limit() -> None:
    items = [
        cand("z-food", category="FOOD", website="https://z.vn", name_en="Z"),
        cand("y-osm", category="RELIGIOUS_SITE"),
        cand("x-osm-hoian", category="RELIGIOUS_SITE", hoi_an=True),
        cand("w-osm-museum", category="MUSEUM"),
        cand("v-osm-site", category="RELIGIOUS_SITE", website="https://v.vn"),
        cand("u-wikidata", wikidata=True),
        cand("t-wikidata-hoian", wikidata=True, hoi_an=True),
        cand("s-wikidata-wiki", wikidata=True, wikipedia=(WIKI,)),
        cand("r-skip", category="NIGHTLIFE"),
    ]
    order = [c.slug for c in prioritise(items, limit=20)]
    assert order == [
        "t-wikidata-hoian",
        "s-wikidata-wiki",
        "u-wikidata",
        "x-osm-hoian",
        "v-osm-site",
        "w-osm-museum",
        "y-osm",
        "z-food",
    ]
    assert [c.slug for c in prioritise(items, limit=2)] == ["t-wikidata-hoian", "s-wikidata-wiki"]


def test_food_and_cafe_are_capped_together() -> None:
    items = [
        cand(f"food-{i}", category="FOOD", website="https://f.vn", name_en="F") for i in range(5)
    ] + [cand(f"cafe-{i}", category="CAFE", has_hours=True, hoi_an=True) for i in range(5)]
    items.append(cand("market", category="MARKET", has_hours=True, hoi_an=True))
    chosen = prioritise(items, limit=50, food_cafe_cap=4)
    assert sum(1 for c in chosen if c.category in ("FOOD", "CAFE")) == 4
    assert "market" in [c.slug for c in chosen]  # MARKET is not in the cap


def test_needs_description() -> None:
    both = {
        "vi": {"summary": "a"},
        "en": {"summary": "b"},
    }
    assert not needs_description(Contributions(wikipedia=both))
    assert needs_description(Contributions(wikipedia={"vi": {"summary": "a"}}))
    sheet = {"description": {"vi": "x", "en": "y"}}
    assert not needs_description(Contributions(sheet=sheet))

"""Enrichment priority (D3, 2026-11-08): tiers, Hội An first, FOOD + CAFE cap, limit."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.agents.schemas import DescriptionSource
from app.curation.auto_publish import Contributions
from app.research.enrich import (
    EnrichCandidate,
    Enricher,
    EnrichReport,
    needs_description,
    prioritise,
    search_query,
)
from app.research.fetch import FetchedPage, FetchStatus
from app.research.tavily import SearchHit, SearchResponse, SearchStatus

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


def test_search_query_scopes_by_area_and_expands_codes() -> None:
    assert search_query(cand("a", name_vi="Chùa Cầu", area_code="hoi-an-old-town")) == (
        "Chùa Cầu Hội An"
    )
    assert search_query(cand("b", name_vi="B1", name_en="My Son B1", area_code="my-son")) == (
        "B1 My Son B1 Thánh địa Mỹ Sơn"
    )
    assert search_query(cand("c", name_vi="Bãi Bụt", area_code="da-nang-center")) == (
        "Bãi Bụt Đà Nẵng"
    )


class _Search:
    async def search(self, query: str) -> SearchResponse:
        hits = (
            SearchHit("https://app.tavily.com/search?q=chua", "Tavily", ""),
            SearchHit("https://webcache.googleusercontent.com/search?q=cache:x", "Cache", ""),
            SearchHit("https://example.vn/redirects-to-bing", "Redirect", ""),
            SearchHit("https://example.vn/chua-cau", "Primary", ""),
        )
        return SearchResponse(query, SearchStatus.OK, hits)


class _Fetcher:
    def __init__(self) -> None:
        self.urls: list[str] = []

    async def fetch(self, url: str) -> FetchedPage:
        self.urls.append(url)
        final = "https://www.bing.com/search?q=x" if "redirects" in url else url
        return FetchedPage(
            url=url,
            status=FetchStatus.OK,
            final_url=final,
            text="Chùa Cầu là cây cầu cổ có mái che ở Hội An.",
            source_revision_id=uuid.uuid4(),
            retrieved_at=datetime(2026, 11, 8, tzinfo=UTC),
        )


async def test_aggregator_and_search_cache_pages_are_never_sources() -> None:
    fetcher = _Fetcher()
    enricher = Enricher(
        settings=None,  # type: ignore[arg-type]
        session_factory=None,  # type: ignore[arg-type]
        ctx=None,  # type: ignore[arg-type]
        fetcher=fetcher,  # type: ignore[arg-type]
        search=_Search(),  # type: ignore[arg-type]
    )
    gathered = await enricher.gather_sources(
        cand("chua-cau", website="https://app.tavily.com/extract"), EnrichReport(provider_key="x")
    )
    assert all("tavily" not in url and "webcache" not in url for url in fetcher.urls)
    assert [s.url for s in gathered.sources] == ["https://example.vn/chua-cau"]

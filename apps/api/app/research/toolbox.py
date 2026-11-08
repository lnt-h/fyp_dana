"""Per-run implementation of :class:`app.agents.schemas.ResearchTools`.

Enforces the per-plan caps (≤ 2 searches, ≤ 3 fetches, ≤ 3 Places checks; FR-099), allows
fetches of search-result URLs only, redacts everything returned to the model and remembers
exactly what the model was shown so quotes can be verified afterwards (DEC-022).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.agents.validators import fold, normalise_url
from app.ai.redaction import redact_text
from app.research.extract import excerpt_for_model
from app.research.fetch import FetchedPage, PageFetcher
from app.research.places_check import PlacesChecker, PlacesCheckResult, PlacesOutcome
from app.research.tavily import SearchResponse, TavilySearch

MAX_SEARCHES = 2
MAX_FETCHES = 3
MAX_PLACES_CHECKS = 3
FETCH_DEADLINE_S = 20.0


@dataclass(frozen=True, slots=True)
class PageRecord:
    """A page fetched in this run: provenance plus the excerpt the model saw."""

    url: str
    title: str | None
    excerpt: str
    source_revision_id: uuid.UUID | None
    retrieved_at: datetime | None
    cached: bool


@dataclass(slots=True)
class ToolStats:
    searches: int = 0
    search_provider_calls: int = 0
    fetches: int = 0
    places_checks: int = 0
    refused: list[str] = field(default_factory=list)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


class ResearchToolbox:
    def __init__(
        self,
        *,
        search: TavilySearch,
        fetcher: PageFetcher,
        places: PlacesChecker,
        focus: str = "",
        max_searches: int = MAX_SEARCHES,
        max_fetches: int = MAX_FETCHES,
        max_places_checks: int = MAX_PLACES_CHECKS,
    ) -> None:
        self._search = search
        self._fetcher = fetcher
        self._places = places
        self._focus = focus
        self._caps = (max_searches, max_fetches, max_places_checks)
        self.stats = ToolStats()
        self.queries: list[str] = []
        self._search_urls: dict[str, str] = {}  # normalised url -> title
        self.pages: dict[str, PageRecord] = {}
        self._search_memo: dict[str, str] = {}
        self.fetch_failures: dict[str, str] = {}
        self._places_by_id: dict[str, PlacesCheckResult] = {}
        self._places_by_name: dict[str, PlacesCheckResult] = {}

    # -- ResearchTools ---------------------------------------------------------------------

    async def tavily_search(self, query: str) -> str:
        memo_key = " ".join(query.casefold().split())
        if memo_key in self._search_memo:  # repeated call (e.g. a retried run): not counted
            return self._search_memo[memo_key]
        if self.stats.searches >= self._caps[0]:
            self.stats.refused.append("search_cap")
            return _json(
                {"error": "search limit reached", "next": "fetch a result URL or answer now"}
            )
        self.stats.searches += 1
        response: SearchResponse = await self._search.search(query)
        if response.provider_called:
            self.stats.search_provider_calls += 1
        if response.query:
            self.queries.append(response.query)
        for hit in response.hits:
            self._search_urls.setdefault(hit.url, hit.title)
        text = _json(
            {
                "status": response.status.value,
                "results": [
                    {
                        "url": hit.url,
                        "title": redact_text(hit.title),
                        "snippet": redact_text(hit.snippet),
                    }
                    for hit in response.hits
                ],
            }
        )
        self._search_memo[memo_key] = text
        return text

    async def fetch_page(self, url: str) -> str:
        normalised = normalise_url(url)
        if normalised in self.pages:
            record = self.pages[normalised]
            return _json({"url": record.url, "title": record.title, "text": record.excerpt})
        if normalised not in self._search_urls:
            self.stats.refused.append("fetch_not_in_results")
            return _json({"error": "only URLs returned by tavily_search can be fetched"})
        if self.stats.fetches >= self._caps[1]:
            self.stats.refused.append("fetch_cap")
            return _json({"error": "page limit reached", "next": "give the final JSON answer now"})
        self.stats.fetches += 1
        try:
            page: FetchedPage = await asyncio.wait_for(
                self._fetcher.fetch(normalised), timeout=FETCH_DEADLINE_S
            )
        except TimeoutError:
            self.fetch_failures[normalised] = "TIMEOUT"
            return _json({"error": "page could not be fetched (TIMEOUT)"})
        if not page.ok:
            self.fetch_failures[normalised] = page.status.value
            return _json({"error": f"page could not be fetched ({page.status.value})"})
        focus = " ".join([self._focus, *self.queries])
        excerpt = excerpt_for_model(page.text, focus=focus)
        record = PageRecord(
            url=normalised,
            title=redact_text(page.title) if page.title else None,
            excerpt=excerpt,
            source_revision_id=page.source_revision_id,
            retrieved_at=page.retrieved_at,
            cached=page.status.value == "CACHED",
        )
        self.pages[normalised] = record
        return _json({"url": normalised, "title": record.title, "text": excerpt})

    async def places_check(self, name: str) -> str:
        key = fold(name)
        if key in self._places_by_name:
            result = self._places_by_name[key]
        elif self.stats.places_checks >= self._caps[2]:
            self.stats.refused.append("places_cap")
            return _json({"outcome": "SKIPPED", "reason": "check limit reached"})
        else:
            self.stats.places_checks += 1
            result = await self._places.check(name)
            self._places_by_name[key] = result
            if result.google_place_id:
                self._places_by_id[result.google_place_id] = result
        return _json({"outcome": result.outcome.value, "place_id": result.google_place_id})

    def page_text(self, url: str) -> str | None:
        record = self.pages.get(normalise_url(url))
        return record.excerpt if record is not None else None

    def search_urls(self) -> frozenset[str]:
        return frozenset(self._search_urls)

    def places_result(self, google_place_id: str) -> str | None:
        result = self._places_by_id.get(google_place_id)
        return result.outcome.value if result is not None else None

    # -- for the candidates repository -----------------------------------------------------

    def page(self, url: str) -> PageRecord | None:
        return self.pages.get(normalise_url(url))

    def places_for(self, name: str, google_place_id: str | None = None) -> PlacesCheckResult:
        if google_place_id and google_place_id in self._places_by_id:
            return self._places_by_id[google_place_id]
        return self._places_by_name.get(fold(name), PlacesCheckResult(PlacesOutcome.SKIPPED))

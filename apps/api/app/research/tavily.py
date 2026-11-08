"""Tavily search adapter (ADR-014, ADR-006 ``tavily`` EPHEMERAL 7 d).

Queries are redacted and scoped to Đà Nẵng, reserved against ``TAVILY_DAY`` and
``TAVILY_MONTH`` and cached in ``research_cache`` (key = SHA-256 of the normalised query).
Only url, title and snippet are kept. Provider errors and caps degrade to an empty result.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from tavily import AsyncTavilyClient  # type: ignore[import-untyped]

from app.agents.validators import normalise_url
from app.ai.quota import Bucket, QuotaLedger
from app.ai.redaction import RedactionError
from app.research.extract import build_scoped_query, query_key
from app.research.store import TAVILY, ResearchStore

logger = logging.getLogger("gonarra.research")

MAX_RESULTS = 5
SNIPPET_CHARS = 160
TIMEOUT_S = 20.0


class SearchStatus(StrEnum):
    OK = "OK"
    CACHED = "CACHED"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    DISABLED = "DISABLED"
    REFUSED = "REFUSED"  # redaction gate


@dataclass(frozen=True, slots=True)
class SearchHit:
    url: str
    title: str
    snippet: str


@dataclass(frozen=True, slots=True)
class SearchResponse:
    query: str
    status: SearchStatus
    hits: tuple[SearchHit, ...] = field(default_factory=tuple)

    @property
    def provider_called(self) -> bool:
        return self.status in {SearchStatus.OK, SearchStatus.PROVIDER_ERROR}


def _hits(payload: dict[str, Any]) -> tuple[SearchHit, ...]:
    hits: list[SearchHit] = []
    for item in payload.get("results") or []:
        url = str(item.get("url") or "")
        if not url.startswith(("https://", "http://")):
            continue
        hits.append(
            SearchHit(
                url=normalise_url(url),
                title=str(item.get("title") or "")[:300],
                snippet=" ".join(str(item.get("content") or "").split())[:SNIPPET_CHARS],
            )
        )
    return tuple(hits[:MAX_RESULTS])


class TavilySearch:
    def __init__(
        self,
        *,
        api_key: str | None,
        ledger: QuotaLedger,
        store: ResearchStore,
        client: AsyncTavilyClient | None = None,
    ) -> None:
        self._ledger = ledger
        self._store = store
        self._client = (
            client if client is not None or not api_key else AsyncTavilyClient(api_key=api_key)
        )

    async def search(self, query: str) -> SearchResponse:
        try:
            scoped = build_scoped_query(query)
        except RedactionError:
            return SearchResponse(query="", status=SearchStatus.REFUSED)
        key = query_key(scoped)
        cached = await self._store.get_cached(TAVILY, key)
        if cached is not None:
            return SearchResponse(scoped, SearchStatus.CACHED, _hits(cached.payload))
        if self._client is None:
            return SearchResponse(scoped, SearchStatus.DISABLED)

        day = await self._ledger.reserve(bucket=Bucket.TAVILY_DAY)
        if day.reservation is None:
            return SearchResponse(scoped, SearchStatus.QUOTA_EXCEEDED)
        month = await self._ledger.reserve(bucket=Bucket.TAVILY_MONTH)
        if month.reservation is None:
            await self._ledger.release(day.reservation)
            return SearchResponse(scoped, SearchStatus.QUOTA_EXCEEDED)

        try:
            payload = await self._client.search(
                scoped,
                search_depth="basic",
                topic="general",
                max_results=MAX_RESULTS,
                include_answer=False,
                include_raw_content=False,
                include_images=False,
                country="vietnam",
                timeout=TIMEOUT_S,
            )
        except Exception as exc:  # SDK raises its own types plus httpx errors
            logger.warning("tavily error=%s", type(exc).__name__)
            payload = None
        finally:
            await self._ledger.commit(day.reservation)
            await self._ledger.commit(month.reservation)
        if not isinstance(payload, dict):
            return SearchResponse(scoped, SearchStatus.PROVIDER_ERROR)

        hits = _hits(payload)
        stored = {
            "query": scoped,
            "results": [{"url": h.url, "title": h.title, "content": h.snippet} for h in hits],
        }
        policy = await self._store.policy_id("tavily")
        if policy is not None:
            await self._store.put_cached(TAVILY, key, stored, policy_id=policy)
        logger.info("tavily status=ok results=%d", len(hits))
        return SearchResponse(scoped, SearchStatus.OK, hits)

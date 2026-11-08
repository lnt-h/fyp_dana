"""Grounded description enrichment end to end (D3): stage → gate → publish, idempotent re-run.

Model, search and page fetches are fakes; the database is real (rolled back per test).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from typing import Any

import pytest
from agno.agent import Agent
from agno.models.message import Message
from agno.run.agent import RunOutput
from agno.run.base import RunStatus
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.agents.runtime import AgentContext
from app.ai.invocations import Purpose
from app.ai.quota import Bucket, QuotaDecision, QuotaReservation
from app.config import Settings, get_settings
from app.curation.auto_publish import auto_publish
from app.curation.embedding import Embedding
from app.ingestion.policies import activate_policy
from app.ingestion.wikidata import WikidataItem, stage_items
from app.ingestion.wikipedia import PageSummary, stage_summaries
from app.models.catalog import PlaceLocalization
from app.research.enrich import Enricher
from app.research.fetch import FetchedPage, FetchStatus
from app.research.tavily import SearchResponse, SearchStatus

pytestmark = pytest.mark.integration
CITY = "da-nang"


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    connection = await engine.connect()
    transaction = await connection.begin()
    db = AsyncSession(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    try:
        yield db
    finally:
        await db.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


class Ledger:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def reserve(self, *, bucket: Bucket, amount: int = 1, account_id: Any = None) -> Any:
        res = QuotaReservation(uuid.uuid4(), bucket, amount, account_id, date(2026, 11, 8))
        return QuotaDecision(True, bucket, 100, res)

    async def commit(self, reservation: QuotaReservation) -> None:
        return None

    async def release(self, reservation: QuotaReservation) -> None:
        return None


class Sink:
    async def execute(self, stmt: Any, params: Any) -> None:
        return None

    async def commit(self) -> None:
        return None


@asynccontextmanager
async def sink_session() -> AsyncIterator[Sink]:
    yield Sink()


class Runner:
    def __init__(self, contents: list[dict[str, Any]]) -> None:
        self.contents = contents
        self.prompts: list[str] = []

    async def __call__(self, agent: Agent, prompt: str) -> RunOutput:
        self.prompts.append(prompt)
        return RunOutput(
            content=json.dumps(self.contents.pop(0)),
            status=RunStatus.completed,
            messages=[Message(role="assistant", content="x")],
        )


class NoSearch:
    async def search(self, query: str) -> SearchResponse:
        return SearchResponse(query, SearchStatus.DISABLED)


class NoFetch:
    async def fetch(self, url: str) -> FetchedPage:
        return FetchedPage(url=url, status=FetchStatus.NETWORK_ERROR)


class FakeEmbedder:
    async def embed(self, text: str) -> Embedding | None:
        return Embedding(vector=[1.0] + [0.0] * 767, model="gemini-embedding-001")


async def test_enrich_stages_ai_summary_and_gate_publishes_it(session: AsyncSession) -> None:
    for key in ("wikidata", "wikipedia", "gonarra_ai_summary"):
        await activate_policy(session, key, f"test terms {key}")
    qid = f"Q9{uuid.uuid4().int % 10**9:09d}"
    name = f"Lai Viễn Kiều thử {qid}"
    await stage_items(
        session,
        city_code=CITY,
        items=[
            WikidataItem(
                qid=qid,
                lng=108.3262,
                lat=15.8771,
                labels={"vi": name},
                descriptions={},
                aliases={},
                sitelinks={"vi": f"Title {qid}"},
                class_labels=("bridge",),
                category="HERITAGE",
            )
        ],
        policy_key="wikidata",
    )
    place_id = uuid.UUID(
        str(
            await session.scalar(
                text(
                    "SELECT i.place_id FROM external_place_identities i JOIN data_providers d "
                    "ON d.id = i.data_provider_id WHERE d.provider_key = 'wikidata' "
                    "AND i.upstream_id = :qid"
                ),
                {"qid": qid},
            )
        )
    )
    page_url = f"https://vi.wikipedia.org/wiki/Title_{qid}"
    await stage_summaries(
        session,
        city_code=CITY,
        summaries=[
            PageSummary(
                place_id=place_id,
                locale="vi",
                title=f"Title {qid}",
                page_url=page_url,
                summary="Cây cầu cổ có mái che ở Hội An, do thương nhân Nhật Bản xây dựng.",
                revision="1",
            )
        ],
    )
    draft = {
        "insufficient_evidence": False,
        "description_vi": "Đây là cây cầu cổ có mái che ở Hội An. "
        "Cầu do thương nhân Nhật Bản dựng.",
        "description_en": "This is an old roofed bridge in Hoi An. Japanese merchants built it.",
        "cited_urls": [page_url],
    }
    runner = Runner([draft])
    settings = Settings(_env_file=None, gemini_api_key="test-key")  # type: ignore[call-arg]
    ctx = AgentContext(
        settings=settings,
        ledger=Ledger(settings),  # type: ignore[arg-type]
        session_factory=sink_session,  # type: ignore[arg-type]
        purpose=Purpose.CONTENT_SUMMARY,
        runner=runner,
    )
    enricher = Enricher(
        settings=settings,
        session_factory=sink_session,  # type: ignore[arg-type]
        ctx=ctx,
        fetcher=NoFetch(),  # type: ignore[arg-type]
        search=NoSearch(),  # type: ignore[arg-type]
    )
    report = await enricher.run(session, city_code=CITY, limit=5, place_ids=[place_id])
    assert (report.selected, report.enriched, report.insufficient) == (1, 1, 0)
    assert page_url.split("/wiki/")[0] in runner.prompts[0]

    published = await auto_publish(
        session, city_code=CITY, embedder=FakeEmbedder(), place_ids=[place_id]
    )
    outcome = published.outcomes[0]
    assert outcome.status == "published", outcome.reasons
    rows = {
        row.locale: row
        for row in (
            await session.scalars(
                select(PlaceLocalization).where(
                    PlaceLocalization.place_id == place_id,
                    PlaceLocalization.review_state == "APPROVED",
                )
            )
        ).all()
    }
    assert rows["vi"].translation_origin == "ORIGINAL"  # Wikipedia wins for VI
    assert rows["en"].translation_origin == "AI_SUMMARY"
    assert rows["en"].description == draft["description_en"]
    assert rows["en"].name == name and rows["en"].name_is_source_fallback

    again = await enricher.run(session, city_code=CITY, limit=5, place_ids=[place_id])
    assert again.selected == 0  # published and already enriched: skipped


async def test_retry_insufficient_reselects_places_with_a_rejected_marker(
    session: AsyncSession,
) -> None:
    for key in ("wikidata", "gonarra_ai_summary"):
        await activate_policy(session, key, f"test terms {key}")
    qid = f"Q8{uuid.uuid4().int % 10**9:09d}"
    await stage_items(
        session,
        city_code=CITY,
        items=[
            WikidataItem(
                qid=qid,
                lng=108.2230,
                lat=16.0600,
                labels={"vi": f"Bảo tàng thử {qid}"},
                descriptions={},
                aliases={},
                sitelinks={},
                class_labels=("museum",),
                category="MUSEUM",
            )
        ],
        policy_key="wikidata",
    )
    place_id = uuid.UUID(
        str(
            await session.scalar(
                text(
                    "SELECT i.place_id FROM external_place_identities i JOIN data_providers d "
                    "ON d.id = i.data_provider_id WHERE d.provider_key = 'wikidata' "
                    "AND i.upstream_id = :qid"
                ),
                {"qid": qid},
            )
        )
    )
    settings = Settings(_env_file=None, gemini_api_key="test-key")  # type: ignore[call-arg]
    ctx = AgentContext(
        settings=settings,
        ledger=Ledger(settings),  # type: ignore[arg-type]
        session_factory=sink_session,  # type: ignore[arg-type]
        purpose=Purpose.CONTENT_SUMMARY,
        runner=Runner([]),
    )
    enricher = Enricher(
        settings=settings,
        session_factory=sink_session,  # type: ignore[arg-type]
        ctx=ctx,
        fetcher=NoFetch(),  # type: ignore[arg-type]
        search=NoSearch(),  # type: ignore[arg-type]
    )
    first = await enricher.run(session, city_code=CITY, limit=5, place_ids=[place_id])
    assert (first.selected, first.no_sources) == (1, 1)  # a REJECTED marker is stored
    plain = await enricher.run(session, city_code=CITY, limit=5, place_ids=[place_id])
    assert plain.selected == 0  # the marker skips it
    retry = await enricher.run(
        session, city_code=CITY, limit=5, place_ids=[place_id], retry_insufficient=True
    )
    assert retry.selected == 1  # --retry-insufficient tries it again

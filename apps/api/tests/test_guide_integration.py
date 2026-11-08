"""Guide API and retrieval SQL against PostgreSQL (``pytest -m integration``).

Requires ``alembic upgrade head``. Each test runs in one outer transaction that is rolled back;
the Guide units of work share that connection through savepoints. The model is scripted (no
provider call). Tests that need the proposed migration (city sessions without a trip, the
``GUIDE_ASK`` idempotency operation) skip on a database without it; the pre-migration test
checks the degraded behaviour instead.
"""

from __future__ import annotations

import json
import random
import string
import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from agno.agent import Agent
from agno.models.message import Message
from agno.run.agent import RunOutput
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import null, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.ai.providers import GEMINI_EMBEDDING
from app.ai.quota import QuotaLedger
from app.api.routes.guide import get_guide_service
from app.catalog.normalize import normalize_search_text
from app.cli import seed_reference_data
from app.config import Settings, get_settings
from app.db.types import ewkt_point
from app.guide.repository import SQLAlchemyGuideStore
from app.guide.retrieval import HybridRetriever, QueryVector
from app.guide.service import GuideService
from app.main import create_app
from app.models.account import Account
from app.models.catalog import (
    FactEvidence,
    Place,
    PlaceAlias,
    PlaceFact,
    PlaceLocalization,
    Source,
    SourceRevision,
)
from app.models.knowledge import KnowledgeChunk, KnowledgeChunkSource
from app.models.reference import City, FactField
from app.security.clerk import get_current_account

pytestmark = pytest.mark.integration

VECTOR = [1.0] + [0.0] * 767


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        ) as db:
            await seed_reference_data(db)
            yield db
        await transaction.rollback()
    await engine.dispose()


class Runner:
    def __init__(self, steps: Sequence[dict[str, Any]]) -> None:
        self.steps = list(steps)
        self.prompts: list[str] = []

    async def __call__(self, agent: Agent, prompt: str) -> RunOutput:
        self.prompts.append(prompt)
        return RunOutput(
            content=json.dumps(self.steps.pop(0)),
            messages=[Message(role="assistant", content="x")],
        )


class FixedEmbedder:
    async def embed(self, question: str, *, account_id: uuid.UUID) -> QueryVector | None:
        return QueryVector(VECTOR, GEMINI_EMBEDDING)


@dataclass
class Fixture:
    session: AsyncSession
    client: AsyncClient
    account_id: uuid.UUID
    runner: Runner
    place_id: uuid.UUID
    token: str
    app: FastAPI


async def create_place(session: AsyncSession, token: str) -> uuid.UUID:
    """Published place with OPENING_HOURS (sourced) and an approved, embedded EN + VI chunk."""
    now = datetime.now(UTC)
    city_id = await session.scalar(select(City.id).where(City.code == "da-nang"))
    assert city_id is not None
    place = Place(
        city_id=city_id,
        slug=f"guide-{uuid.uuid4().hex[:12]}",
        category_code="RELIGIOUS_SITE",
        workflow_state="READY_TO_PUBLISH",
        location=ewkt_point(108.2772, 16.1003),
        visit_minutes_min=30,
        visit_minutes_suggested=60,
        visit_minutes_max=90,
        has_no_media=True,
    )
    session.add(place)
    await session.flush()
    names = {"vi": f"Chùa Linh Ứng {token}", "en": f"Linh Ung Pagoda {token}"}
    for locale, name in names.items():
        session.add(
            PlaceLocalization(
                place_id=place.id,
                locale=locale,
                localization_revision=1,
                name=name,
                short_description=f"short {locale}",
                description=f"description {locale}",
                translation_origin="ORIGINAL",
                review_state="APPROVED",
                reviewed_at=now,
            )
        )
        session.add(
            PlaceAlias(
                place_id=place.id,
                locale=locale,
                alias_kind="NAME",
                alias=name,
                alias_normalized=normalize_search_text(name),
                review_state="APPROVED",
            )
        )
    source = Source(
        publisher="Sở Du lịch Đà Nẵng",
        source_kind="OFFICIAL",
        license_code="ALL-RIGHTS-RESERVED",
        attribution_text="© Sở Du lịch Đà Nẵng",
        homepage_url="https://example.invalid",
    )
    session.add(source)
    await session.flush()
    revisions = []
    for index in range(3):
        revision = SourceRevision(
            source_id=source.id,
            locator=f"https://example.invalid/{place.id}/{index}",
            title="Thông tin điểm đến",
            retrieved_at=now,
        )
        session.add(revision)
        revisions.append(revision)
    await session.flush()
    required = (
        await session.scalars(select(FactField.code).where(FactField.required_for_publication))
    ).all()
    for code in required:
        known = code == "OPENING_HOURS"
        fact = PlaceFact(
            place_id=place.id,
            field_code=code,
            fact_revision=1,
            knowledge_state="KNOWN" if known else "UNKNOWN",
            value={"text": "06:00-21:00"} if known else null(),
            verified_at=now,
            review_state="APPROVED",
        )
        session.add(fact)
        await session.flush()
        session.add(
            FactEvidence(
                place_fact_id=fact.id, source_revision_id=revisions[0].id, supported_claim=code
            )
        )
    contents = {
        "en": f"The pagoda {token} has a 67 m Lady Buddha statue facing the sea.",
        "vi": f"Chùa {token} có tượng Phật Bà Quan Âm cao 67 m hướng ra biển.",
    }
    for index, (locale, content) in enumerate(contents.items(), start=1):
        chunk = KnowledgeChunk(
            city_id=city_id,
            place_id=place.id,
            scope="PLACE",
            locale=locale,
            section="OVERVIEW",
            corpus_revision=1,
            chunk_index=0,
            content=content,
            content_sha256=uuid.uuid4().hex + uuid.uuid4().hex,
            embedding=VECTOR,
            embedding_model=GEMINI_EMBEDDING,
            review_state="APPROVED",
        )
        session.add(chunk)
        await session.flush()
        session.add(
            KnowledgeChunkSource(
                knowledge_chunk_id=chunk.id, source_revision_id=revisions[index].id
            )
        )
    await session.flush()
    await session.execute(text("SELECT fn_publish_place(:place_id, NULL)"), {"place_id": place.id})
    return place.id


async def _constraint(session: AsyncSession, name: str) -> str | None:
    value = await session.scalar(
        text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = :name"),
        {"name": name},
    )
    return str(value) if value is not None else None


@pytest.fixture
async def fx(session: AsyncSession) -> AsyncIterator[Fixture]:
    token = "".join(random.choices(string.ascii_lowercase, k=8))
    account = Account(clerk_user_id=f"user_guide_{token}")
    session.add(account)
    await session.flush()
    place_id = await create_place(session, token)

    @asynccontextmanager
    async def shared() -> AsyncIterator[AsyncSession]:
        yield session

    @asynccontextmanager
    async def uow() -> AsyncIterator[SQLAlchemyGuideStore]:
        yield SQLAlchemyGuideStore(session)

    settings = Settings(_env_file=None, gemini_api_key="gem-test", groq_api_key="groq-test")  # type: ignore[call-arg]
    runner = Runner([])
    service = GuideService(
        settings=settings,
        uow=uow,  # type: ignore[arg-type]
        session_factory=shared,
        retriever=HybridRetriever(FixedEmbedder()),
        ledger=QuotaLedger(shared, settings),
        runner=runner,
    )
    app = create_app()
    app.dependency_overrides[get_guide_service] = lambda: service
    # A transient copy: a rollback inside the shared session must not expire the caller's account.
    caller = Account(id=account.id, clerk_user_id=account.clerk_user_id)
    app.dependency_overrides[get_current_account] = lambda: caller
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield Fixture(session, client, caller.id, runner, place_id, token, app)


async def test_place_session_answer_is_stored_with_citations(fx: Fixture) -> None:
    created = await fx.client.post(
        "/v1/ai/sessions", json={"scope": "PLACE", "place_id": str(fx.place_id), "locale": "en"}
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["id"]
    assert created.json()["city_code"] == "da-nang"

    fx.runner.steps.append(
        {
            "status": "ANSWERED",
            "claims": [
                {"text": "It has a 67 m Lady Buddha statue.", "evidence_ids": ["E1"]},
                {"text": "It opens 06:00-21:00.", "evidence_ids": ["E2"]},
            ],
        }
    )
    asked = await fx.client.post(
        f"/v1/ai/sessions/{session_id}/messages",
        json={"content": "What is there and when does it open?", "input_mode": "TEXT"},
        headers={"Idempotency-Key": str(uuid.uuid4())},  # degrades without GUIDE_ASK
    )
    assert asked.status_code == 200, asked.text
    answer = asked.json()
    assert answer["answer_status"] == "ANSWERED"
    kinds = sorted(c["evidence_kind"] for c in answer["citations"])
    assert kinds == ["CHUNK", "FACT"]
    chunk = next(c for c in answer["citations"] if c["evidence_kind"] == "CHUNK")
    assert chunk["section"] == "OVERVIEW" and chunk["publisher"] == "Sở Du lịch Đà Nẵng"
    assert chunk["verified_at"] and chunk["trust_level"] == "VERIFIED"
    payload = json.loads(fx.runner.prompts[0])
    assert fx.token in payload["evidence"][0]["text"]  # Tier 1: session-locale chunk first
    assert "Lady Buddha" in payload["evidence"][0]["text"]

    page = await fx.client.get(f"/v1/ai/sessions/{session_id}/messages", params={"limit": 1})
    body = page.json()
    assert [m["role"] for m in body["items"]] == ["TRAVELER"] and body["next_cursor"]
    rest = await fx.client.get(
        f"/v1/ai/sessions/{session_id}/messages", params={"cursor": body["next_cursor"]}
    )
    stored = rest.json()["items"]
    assert [m["seq"] for m in stored] == [2] and stored[0]["citations"] == answer["citations"]
    invocations = await fx.session.scalar(
        text(
            "SELECT count(*) FROM ai_invocations WHERE account_id = :a AND purpose = 'GUIDE_ANSWER'"
        ),
        {"a": fx.account_id},
    )
    assert invocations == 1

    other = Account(id=uuid.uuid4(), clerk_user_id=f"user_other_{fx.token}")
    fx.app.dependency_overrides[get_current_account] = lambda: other
    assert (await fx.client.get(f"/v1/ai/sessions/{session_id}")).status_code == 404


async def test_city_retrieval_sql_entity_lexical_vector(fx: Fixture) -> None:
    city_id = await fx.session.scalar(select(City.id).where(City.code == "da-nang"))
    assert city_id is not None
    store = SQLAlchemyGuideStore(fx.session)
    retriever = HybridRetriever(FixedEmbedder())
    result = await retriever.for_city(
        store,
        city_id=city_id,
        question=f"linh ung pagoda {fx.token} opening hours?",
        locale="en",
        account_id=fx.account_id,
    )
    assert result.channels["entity"] == 3  # EN chunk, VI chunk, OPENING_HOURS fact
    assert result.channels["vector"] >= 1
    keys = [item.key for item in result.evidence]
    assert keys and all(item.source_revision_id for item in result.evidence)
    assert any(item.field_code == "OPENING_HOURS" for item in result.evidence)
    assert result.evidence[0].kind == "CHUNK"  # found by entity, lexical and vector

    lexical = await store.lexical_chunks(city_id, [f"%{fx.token}%"], ["vi", "en"], 5)
    assert {item.locale for item in lexical} == {"vi", "en"}
    assert GEMINI_EMBEDDING in await store.embedding_models(city_id)


async def test_city_session_before_migration_is_refused_cleanly(fx: Fixture) -> None:
    if await _constraint(fx.session, "ck_guide_sessions_context") is None:
        pytest.skip("migration 0008 applied: city sessions without a trip are allowed")
    response = await fx.client.post("/v1/ai/sessions", json={"scope": "CITY", "locale": "vi"})
    assert response.status_code == 503, response.text


async def test_city_session_answer_and_idempotent_replay(fx: Fixture) -> None:
    if await _constraint(fx.session, "ck_guide_sessions_context") is not None:
        pytest.skip("needs migration 0008 (city sessions without a trip)")
    operations = await _constraint(fx.session, "ck_idempotency_records_operation") or ""
    if "'GUIDE_ASK'" not in operations:
        pytest.skip("needs migration 0008 (GUIDE_ASK idempotency operation)")
    created = await fx.client.post(
        "/v1/ai/sessions", json={"scope": "CITY", "city_code": "da-nang", "locale": "en"}
    )
    assert created.status_code == 201, created.text
    assert created.json()["scope"] == "CITY" and created.json()["place_id"] is None
    session_id = created.json()["id"]
    fx.runner.steps.append(
        {"status": "ANSWERED", "claims": [{"text": "Open 06:00-21:00.", "evidence_ids": ["E1"]}]}
    )
    url = f"/v1/ai/sessions/{session_id}/messages"
    body = {"content": f"Linh Ung Pagoda {fx.token} opening hours?", "input_mode": "TEXT"}
    key = {"Idempotency-Key": str(uuid.uuid4())}
    first = await fx.client.post(url, json=body, headers=key)
    assert first.status_code == 200, first.text
    citations = first.json()["citations"]
    assert len(citations) == 1 and citations[0]["trust_level"] == "VERIFIED"
    again = await fx.client.post(url, json=body, headers=key)
    assert again.json()["id"] == first.json()["id"] and len(fx.runner.prompts) == 1
    items = (await fx.client.get(url)).json()["items"]
    assert [m["role"] for m in items] == ["TRAVELER", "ASSISTANT"]

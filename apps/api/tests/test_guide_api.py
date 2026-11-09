"""Guide API (API-024..028) against an in-memory store and a scripted model runner.

The writer runs through the real shared runtime (``run_chain``: redactor, quota ledger,
invocation metadata, Pydantic validation); only ``agent.arun`` is replaced.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from collections import Counter
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from agno.agent import Agent
from agno.models.message import Message
from agno.run.agent import RunOutput
from httpx import ASGITransport, AsyncClient

from app.ai.quota import Bucket, QuotaDecision, QuotaReservation
from app.api.routes.guide import get_guide_service
from app.config import Settings
from app.guide.evidence import Evidence, PlaceName
from app.guide.retrieval import HybridRetriever
from app.guide.service import GuideService
from app.guide.store import CitationRow, CityRef, SessionRecord
from app.main import create_app
from app.models.account import Account
from app.models.planning import IdempotencyRecord
from app.schemas.guide import Citation, GuideMessage
from app.security.clerk import get_current_account

NOW = datetime(2026, 11, 8, 9, 0, tzinfo=UTC)
UUID_RE = re.compile(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}")


# ---- fakes --------------------------------------------------------------------------------------


class FakeLedger:
    def __init__(self, settings: Settings, caps: dict[Bucket, int] | None = None) -> None:
        self.settings = settings
        self.caps = caps or {}
        self.used: Counter[Bucket] = Counter()
        self.reserved: Counter[Bucket] = Counter()

    async def reserve(
        self, *, bucket: Bucket, amount: int = 1, account_id: uuid.UUID | None = None
    ) -> QuotaDecision:
        cap = self.caps.get(bucket, 1000)
        if self.used[bucket] + self.reserved[bucket] + amount > cap:
            return QuotaDecision(allowed=False, bucket=bucket, remaining=0)
        self.reserved[bucket] += amount
        res = QuotaReservation(uuid.uuid4(), bucket, amount, account_id, date(2026, 11, 8))
        return QuotaDecision(True, bucket, cap - self.used[bucket], res)

    async def commit(self, reservation: QuotaReservation) -> None:
        self.reserved[reservation.bucket] -= reservation.amount
        self.used[reservation.bucket] += reservation.amount

    async def release(self, reservation: QuotaReservation) -> None:
        self.reserved[reservation.bucket] -= reservation.amount


class _InvocationSession:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    async def execute(self, stmt: Any, params: dict[str, Any]) -> None:
        self.rows.append(dict(params))

    async def commit(self) -> None:
        return None


class Runner:
    """Replaces ``agent.arun``: scripted outputs (dict → JSON, Exception → raised)."""

    def __init__(self, steps: Sequence[Any]) -> None:
        self.steps = list(steps)
        self.prompts: list[str] = []

    async def __call__(self, agent: Agent, prompt: str) -> RunOutput:
        self.prompts.append(prompt)
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        return RunOutput(
            content=json.dumps(step), messages=[Message(role="assistant", content="x")]
        )


@dataclass
class StoredMessage:
    id: uuid.UUID
    session_id: uuid.UUID
    seq: int
    role: str
    input_mode: str | None
    content: str
    answer_status: str | None
    citations: list[CitationRow]
    created_at: datetime


@dataclass
class FakeDb:
    city: CityRef
    places: dict[uuid.UUID, PlaceName] = field(default_factory=dict)
    evidence: dict[uuid.UUID, list[Evidence]] = field(default_factory=dict)
    lexical: list[Evidence] = field(default_factory=list)
    sessions: dict[uuid.UUID, SessionRecord] = field(default_factory=dict)
    messages: dict[uuid.UUID, StoredMessage] = field(default_factory=dict)
    idem: dict[tuple[uuid.UUID, str, str], IdempotencyRecord] = field(default_factory=dict)
    trips: dict[uuid.UUID, tuple[uuid.UUID, uuid.UUID]] = field(default_factory=dict)


class FakeStore:
    def __init__(self, db: FakeDb) -> None:
        self.db = db

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None

    async def enabled_city(self, code: str) -> CityRef | None:
        return self.db.city if code == self.db.city.code else None

    async def city(self, city_id: uuid.UUID) -> CityRef | None:
        return self.db.city if city_id == self.db.city.id else None

    async def published_place_city(self, place_id: uuid.UUID) -> uuid.UUID | None:
        return self.db.city.id if place_id in self.db.places else None

    async def owned_trip_city(self, trip_id: uuid.UUID, account_id: uuid.UUID) -> uuid.UUID | None:
        owner = self.db.trips.get(trip_id)
        return owner[1] if owner and owner[0] == account_id else None

    async def insert_session(self, **kw: Any) -> SessionRecord:
        record = SessionRecord(id=uuid.uuid4(), created_at=NOW, **kw)
        self.db.sessions[record.id] = record
        return record

    async def get_session(
        self, session_id: uuid.UUID, account_id: uuid.UUID, *, lock: bool = False
    ) -> SessionRecord | None:
        record = self.db.sessions.get(session_id)
        return record if record and record.account_id == account_id else None

    async def delete_session(self, session_id: uuid.UUID) -> None:
        self.db.sessions.pop(session_id, None)
        for mid in [m.id for m in self.db.messages.values() if m.session_id == session_id]:
            del self.db.messages[mid]

    def _of(self, session_id: uuid.UUID) -> list[StoredMessage]:
        return sorted(
            (m for m in self.db.messages.values() if m.session_id == session_id),
            key=lambda m: m.seq,
        )

    async def next_seq(self, session_id: uuid.UUID) -> int:
        return max((m.seq for m in self._of(session_id)), default=0) + 1

    async def add_message(self, *, citations: Sequence[CitationRow] = (), **kw: Any) -> uuid.UUID:
        assert 1 <= len(kw["content"]) <= 4000
        message = StoredMessage(id=uuid.uuid4(), citations=list(citations), created_at=NOW, **kw)
        message_keys = {(message.session_id, m.seq) for m in self.db.messages.values()}
        assert (message.session_id, message.seq) not in message_keys
        revisions = [c.source_revision_id for c in citations]
        assert len(revisions) == len(set(revisions)), "citation PK is (message, revision)"
        self.db.messages[message.id] = message
        return message.id

    async def delete_message(self, message_id: uuid.UUID) -> None:
        self.db.messages.pop(message_id, None)

    def _schema(self, m: StoredMessage) -> GuideMessage:
        by_revision = {
            e.source_revision_id: e for items in self.db.evidence.values() for e in items
        }
        by_revision.update({e.source_revision_id: e for e in self.db.lexical})
        citations = []
        for c in m.citations:
            item = by_revision[c.source_revision_id]
            citations.append(
                Citation(
                    source_revision_id=c.source_revision_id,
                    trust_level="VERIFIED",
                    evidence_kind=item.kind,
                    knowledge_chunk_id=c.knowledge_chunk_id,
                    place_fact_id=c.place_fact_id,
                    section="OVERVIEW" if item.kind == "CHUNK" else None,
                    publisher=item.publisher,
                    verified_at=item.verified_at,
                )
            )
        return GuideMessage.model_validate(
            {
                "id": m.id,
                "seq": m.seq,
                "role": m.role,
                "input_mode": m.input_mode,
                "content": m.content,
                "answer_status": m.answer_status,
                "citations": citations,
                "created_at": m.created_at,
            }
        )

    async def list_messages(
        self, session_id: uuid.UUID, *, after_seq: int, limit: int
    ) -> list[GuideMessage]:
        return [self._schema(m) for m in self._of(session_id) if m.seq > after_seq][:limit]

    async def get_message(self, message_id: uuid.UUID) -> GuideMessage | None:
        m = self.db.messages.get(message_id)
        return self._schema(m) if m else None

    async def recent_turns(
        self, session_id: uuid.UUID, *, before_seq: int, limit: int
    ) -> list[tuple[str, str]]:
        rows = [(m.role, m.content) for m in self._of(session_id) if m.seq < before_seq]
        return rows[-limit:]

    async def claim_idempotency(
        self, account_id: uuid.UUID, operation: str, key: str, sha: str, expires_at: datetime
    ) -> IdempotencyRecord | None:
        scope = (account_id, operation, key)
        if scope in self.db.idem:
            return self.db.idem[scope]
        self.db.idem[scope] = IdempotencyRecord(
            account_id=account_id,
            operation=operation,
            idempotency_key=key,
            request_sha256=sha,
            state="IN_PROGRESS",
            expires_at=expires_at,
        )
        return None

    async def complete_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        *,
        status: int,
        body: dict[str, Any],
        resource_id: uuid.UUID | None,
    ) -> None:
        record = self.db.idem[(account_id, operation, key)]
        record.state, record.response_status, record.response_body = "COMPLETED", status, body

    async def release_idempotency(self, account_id: uuid.UUID, operation: str, key: str) -> None:
        record = self.db.idem.get((account_id, operation, key))
        if record is not None and record.state == "IN_PROGRESS":
            del self.db.idem[(account_id, operation, key)]

    # evidence source
    async def place_names(self, city_id: uuid.UUID) -> list[PlaceName]:
        return list(self.db.places.values())

    async def place_evidence(
        self, place_ids: Sequence[uuid.UUID], locales: Sequence[str]
    ) -> list[Evidence]:
        return [
            e
            for pid in place_ids
            for e in self.db.evidence.get(pid, [])
            if e.kind == "FACT" or e.locale in locales
        ]

    async def lexical_chunks(
        self, city_id: uuid.UUID, patterns: Any, locales: Any, limit: int
    ) -> list[Evidence]:
        return self.db.lexical[:limit]

    async def embedding_models(self, city_id: uuid.UUID) -> set[str]:
        return set()

    async def vector_chunks(self, *args: Any) -> list[Evidence]:  # pragma: no cover
        raise AssertionError("no embeddings in the fake")


def fact(place: PlaceName, field_code: str, text: str) -> Evidence:
    fid = uuid.uuid4()
    return Evidence(
        key=f"fact:{fid}",
        kind="FACT",
        place_id=place.place_id,
        text=text,
        source_revision_id=uuid.uuid4(),
        publisher="Ban quản lý",
        title=None,
        locator="https://example.vn/hours",
        verified_at=date(2026, 11, 1),
        place_fact_id=fid,
        field_code=field_code,
        label=place.display_vi,
    )


def chunk(place: PlaceName | None, text: str, locale: str = "en") -> Evidence:
    cid = uuid.uuid4()
    return Evidence(
        key=f"chunk:{cid}",
        kind="CHUNK",
        place_id=place.place_id if place else None,
        text=text,
        source_revision_id=uuid.uuid4(),
        publisher="Wikipedia",
        title="Article",
        locator="https://en.wikipedia.org/wiki/X",
        verified_at=date(2026, 11, 2),
        knowledge_chunk_id=cid,
        section="OVERVIEW",
        locale=locale,
        label=place.display_vi if place else None,
    )


@dataclass
class World:
    db: FakeDb
    account_id: uuid.UUID
    settings: Settings
    ledger: FakeLedger
    runner: Runner
    invocations: list[dict[str, Any]]
    client: AsyncClient
    pagoda: PlaceName

    def script(self, *steps: Any) -> None:
        self.runner.steps.extend(steps)

    def session(
        self, *, place: PlaceName | None = None, account: uuid.UUID | None = None
    ) -> SessionRecord:
        record = SessionRecord(
            id=uuid.uuid4(),
            account_id=account or self.account_id,
            trip_id=None,
            place_id=place.place_id if place else None,
            locale="en",
            expires_at=NOW + timedelta(days=30),
            created_at=NOW,
        )
        self.db.sessions[record.id] = record
        return record


@pytest.fixture
async def world() -> AsyncIterator[World]:
    settings = Settings(_env_file=None, gemini_api_key="gem-test", groq_api_key="groq-test")  # type: ignore[call-arg]
    db = FakeDb(city=CityRef(uuid.uuid4(), "da-nang"))
    pagoda = PlaceName(
        uuid.uuid4(), ("Chùa Linh Ứng", "Linh Ung Pagoda"), "Chùa Linh Ứng", "Linh Ung Pagoda"
    )
    db.places[pagoda.place_id] = pagoda
    db.evidence[pagoda.place_id] = [
        fact(pagoda, "OPENING_HOURS", "Opening hours: 06:00-21:00 daily"),
        chunk(pagoda, "Linh Ung Pagoda on the Son Tra peninsula has a 67 m Lady Buddha statue."),
    ]
    account_id = uuid.uuid4()
    ledger = FakeLedger(settings)
    runner = Runner([])
    invocations: list[dict[str, Any]] = []

    @asynccontextmanager
    async def invocation_session() -> AsyncIterator[_InvocationSession]:
        yield _InvocationSession(invocations)

    @asynccontextmanager
    async def uow() -> AsyncIterator[FakeStore]:
        yield FakeStore(db)

    service = GuideService(
        settings=settings,
        uow=uow,  # type: ignore[arg-type]
        session_factory=invocation_session,
        retriever=HybridRetriever(None),
        ledger=ledger,  # type: ignore[arg-type]
        runner=runner,
        clock=lambda: NOW,
    )
    app = create_app()
    app.dependency_overrides[get_guide_service] = lambda: service
    app.dependency_overrides[get_current_account] = lambda: Account(
        id=account_id, clerk_user_id="user_a"
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield World(db, account_id, settings, ledger, runner, invocations, client, pagoda)


SSE = {"accept": "text/event-stream"}


def parse_sse(body: str) -> list[dict[str, Any]]:
    events = []
    for block in body.split("\n\n"):
        lines = [line for line in block.splitlines() if not line.startswith(":")]
        if not lines:
            continue
        name = lines[0].removeprefix("event: ")
        data = json.loads(lines[1].removeprefix("data: "))
        assert data["type"] == name
        events.append(data)
    return events


def answer(*claims: tuple[str, list[str]]) -> dict[str, Any]:
    return {
        "status": "ANSWERED",
        "claims": [{"text": text, "evidence_ids": ids} for text, ids in claims],
    }


# ---- authentication and ownership ---------------------------------------------------------------


async def test_every_guide_route_requires_a_token() -> None:
    sid = uuid.uuid4()
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as c:
        responses = [
            await c.post("/v1/ai/sessions", json={"scope": "CITY", "locale": "vi"}),
            await c.get(f"/v1/ai/sessions/{sid}"),
            await c.delete(f"/v1/ai/sessions/{sid}"),
            await c.get(f"/v1/ai/sessions/{sid}/messages"),
            await c.post(
                f"/v1/ai/sessions/{sid}/messages", json={"content": "hi", "input_mode": "TEXT"}
            ),
        ]
    for response in responses:
        assert response.status_code == 401, response.text


async def test_another_accounts_session_is_not_found(world: World) -> None:
    foreign = world.session(account=uuid.uuid4())
    base = f"/v1/ai/sessions/{foreign.id}"
    responses = [
        await world.client.get(base),
        await world.client.get(f"{base}/messages"),
        await world.client.post(
            f"{base}/messages", json={"content": "Opening hours?", "input_mode": "TEXT"}
        ),
        await world.client.delete(base),
    ]
    for response in responses:
        assert response.status_code == 404, response.text
        assert response.json()["error"]["code"] == "resource_not_found"
    assert foreign.id in world.db.sessions and not world.db.messages
    assert not world.runner.prompts


async def test_expired_session_is_not_found(world: World) -> None:
    record = world.session()
    world.db.sessions[record.id] = replace(record, expires_at=NOW - timedelta(seconds=1))
    assert (await world.client.get(f"/v1/ai/sessions/{record.id}")).status_code == 404


# ---- sessions -----------------------------------------------------------------------------------


async def test_create_city_and_place_sessions(world: World) -> None:
    city = await world.client.post(
        "/v1/ai/sessions", json={"scope": "CITY", "city_code": "da-nang", "locale": "en"}
    )
    assert city.status_code == 201, city.text
    body = city.json()
    assert body["scope"] == "CITY" and body["city_code"] == "da-nang" and body["place_id"] is None
    assert world.db.sessions[uuid.UUID(body["id"])].account_id == world.account_id

    default_city = await world.client.post(
        "/v1/ai/sessions", json={"scope": "CITY", "locale": "vi"}
    )
    assert default_city.json()["city_code"] == "da-nang"

    place = await world.client.post(
        "/v1/ai/sessions",
        json={"scope": "PLACE", "place_id": str(world.pagoda.place_id), "locale": "vi"},
    )
    assert place.status_code == 201
    assert place.json()["scope"] == "PLACE" and place.json()["place_id"] == str(
        world.pagoda.place_id
    )

    fetched = await world.client.get(f"/v1/ai/sessions/{body['id']}")
    assert fetched.status_code == 200 and fetched.json()["id"] == body["id"]


@pytest.mark.parametrize(
    ("payload", "status"),
    [
        ({"scope": "PLACE", "locale": "vi"}, 422),
        ({"scope": "CITY", "place_id": str(uuid.uuid4()), "locale": "vi"}, 422),
        ({"scope": "PLACE", "place_id": str(uuid.uuid4()), "locale": "vi"}, 404),
        ({"scope": "CITY", "city_code": "ha-noi", "locale": "vi"}, 404),
        ({"scope": "CITY", "locale": "fr"}, 422),
        ({"scope": "CITY", "locale": "vi", "extra": 1}, 422),
        ({"scope": "CITY", "locale": "vi", "trip_id": str(uuid.uuid4())}, 404),
    ],
)
async def test_create_session_rejects_bad_bodies(
    world: World, payload: dict[str, Any], status: int
) -> None:
    response = await world.client.post("/v1/ai/sessions", json=payload)
    assert response.status_code == status, response.text
    assert not world.db.sessions


async def test_delete_session(world: World) -> None:
    record = world.session()
    response = await world.client.delete(f"/v1/ai/sessions/{record.id}")
    assert response.status_code == 204 and record.id not in world.db.sessions


# ---- messages page ------------------------------------------------------------------------------


async def test_messages_are_paginated_by_seq(world: World) -> None:
    record = world.session()
    store = FakeStore(world.db)
    for seq in range(1, 6):
        await store.add_message(
            session_id=record.id,
            seq=seq,
            role="TRAVELER" if seq % 2 else "ASSISTANT",
            input_mode="TEXT" if seq % 2 else None,
            content=f"m{seq}",
            answer_status=None if seq % 2 else "INSUFFICIENT_EVIDENCE",
        )
    url = f"/v1/ai/sessions/{record.id}/messages"
    seen: list[int] = []
    cursor: str | None = None
    while True:
        params: dict[str, Any] = {"limit": 2, **({"cursor": cursor} if cursor else {})}
        page = (await world.client.get(url, params=params)).json()
        seen += [item["seq"] for item in page["items"]]
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert seen == [1, 2, 3, 4, 5]

    assert (await world.client.get(url, params={"cursor": "garbage!"})).status_code == 400
    other = world.session()
    foreign_cursor = (await world.client.get(url, params={"limit": 1})).json()["next_cursor"]
    bad = await world.client.get(
        f"/v1/ai/sessions/{other.id}/messages", params={"cursor": foreign_cursor}
    )
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "invalid_cursor"
    assert (await world.client.get(url, params={"limit": 51})).status_code == 422


# ---- asking -------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {"content": "", "input_mode": "TEXT"},
        {"content": "   ", "input_mode": "TEXT"},
        {"content": "x" * 4001, "input_mode": "TEXT"},
        {"content": "hi", "input_mode": "PHOTO"},
        {"content": "hi", "input_mode": "TEXT", "account_id": "x"},
    ],
)
async def test_question_validation(world: World, payload: dict[str, Any]) -> None:
    record = world.session()
    response = await world.client.post(f"/v1/ai/sessions/{record.id}/messages", json=payload)
    assert response.status_code == 422
    assert not world.db.messages


async def test_city_question_streams_progress_text_and_cited_result(world: World) -> None:
    record = world.session()
    world.script(
        answer(
            ("Linh Ung Pagoda opens 06:00-21:00 daily.", ["E1"]),
            ("It has a 67 m Lady Buddha statue.", ["E2"]),
        )
    )
    response = await world.client.post(
        f"/v1/ai/sessions/{record.id}/messages",
        json={"content": "When does Linh Ung Pagoda open?", "input_mode": "TEXT"},
        headers={**SSE, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    kinds = [(e["type"], e.get("stage")) for e in events]
    assert kinds == [
        ("progress", "VALIDATING"),
        ("progress", "RETRIEVING"),
        ("progress", "ANSWERING"),
        ("text", None),
        ("text", None),
        ("result", None),
    ]
    message = events[-1]["message"]
    assert message["role"] == "ASSISTANT" and message["answer_status"] == "ANSWERED"
    assert message["content"] == "".join(e["delta"] for e in events if e["type"] == "text")
    assert {c["evidence_kind"] for c in message["citations"]} == {"FACT", "CHUNK"}
    assert all(c["trust_level"] == "VERIFIED" and c["url"] is None for c in message["citations"])

    stored = (await world.client.get(f"/v1/ai/sessions/{record.id}/messages")).json()["items"]
    assert [(m["seq"], m["role"]) for m in stored] == [(1, "TRAVELER"), (2, "ASSISTANT")]
    assert stored[1]["id"] == message["id"] and stored[1]["citations"] == message["citations"]

    # BR-046: the prompt carries no account id or catalog UUID; evidence ids are positional.
    prompt = world.runner.prompts[0]
    assert str(world.account_id) not in prompt and not UUID_RE.search(prompt)
    assert world.ledger.used[Bucket.ACCOUNT_QUESTIONS] == 1
    assert world.invocations and world.invocations[0]["purpose"] == "GUIDE_ANSWER"
    assert world.invocations[0]["account_id"] == world.account_id


async def test_place_session_uses_tier1_evidence_and_json_mode(world: World) -> None:
    record = world.session(place=world.pagoda)
    world.script(answer(("It opens at 6am.", ["E2"])))
    response = await world.client.post(
        f"/v1/ai/sessions/{record.id}/messages",
        json={"content": "When does it open?", "input_mode": "VOICE_TRANSCRIPT"},
    )
    assert response.status_code == 200, response.text
    message = response.json()
    assert message["answer_status"] == "ANSWERED" and len(message["citations"]) == 1
    payload = json.loads(world.runner.prompts[0])
    assert [item["evidence_id"] for item in payload["evidence"]] == ["E1", "E2"]
    traveler = next(m for m in world.db.messages.values() if m.role == "TRAVELER")
    assert traveler.input_mode == "VOICE_TRANSCRIPT"


async def test_invalid_citations_are_dropped(world: World) -> None:
    record = world.session()
    world.script(
        answer(
            ("Opens at 06:00.", ["E1"]), ("Free entry for all.", ["E7"]), ("Mixed.", ["E1", "X"])
        )
    )
    response = await world.client.post(
        f"/v1/ai/sessions/{record.id}/messages",
        json={"content": "Linh Ung Pagoda hours?", "input_mode": "TEXT"},
    )
    message = response.json()
    assert message["content"] == "Opens at 06:00."
    assert len(message["citations"]) == 1 and message["citations"][0]["evidence_kind"] == "FACT"


async def test_answer_without_valid_citation_is_insufficient_evidence(world: World) -> None:
    record = world.session()
    world.script(answer(("Made up.", ["E9"])))
    response = await world.client.post(
        f"/v1/ai/sessions/{record.id}/messages",
        json={"content": "Linh Ung Pagoda hours?", "input_mode": "TEXT"},
        headers=SSE,
    )
    events = parse_sse(response.text)
    assert not [e for e in events if e["type"] == "text"]
    message = events[-1]["message"]
    assert message["answer_status"] == "INSUFFICIENT_EVIDENCE" and message["citations"] == []
    assert message["content"]


async def test_no_evidence_answers_insufficient_without_a_model_call(world: World) -> None:
    record = world.session()
    response = await world.client.post(
        f"/v1/ai/sessions/{record.id}/messages",
        json={"content": "Best pho in Hanoi?", "input_mode": "TEXT"},
        headers=SSE,
    )
    events = parse_sse(response.text)
    assert [e.get("stage") for e in events if e["type"] == "progress"] == [
        "VALIDATING",
        "RETRIEVING",
    ]
    assert events[-1]["message"]["answer_status"] == "INSUFFICIENT_EVIDENCE"
    assert not world.runner.prompts and not world.invocations
    assert world.ledger.used[Bucket.ACCOUNT_QUESTIONS] == 0
    assert len(world.db.messages) == 2


async def test_idempotent_retry_replays_the_stored_answer(world: World) -> None:
    record = world.session()
    world.script(answer(("Opens at 06:00.", ["E1"])))
    key = {"Idempotency-Key": str(uuid.uuid4())}
    body = {"content": "Linh Ung Pagoda hours?", "input_mode": "TEXT"}
    url = f"/v1/ai/sessions/{record.id}/messages"
    first = await world.client.post(url, json=body, headers=key)
    again = await world.client.post(url, json=body, headers={**key, **SSE})
    assert first.status_code == 200
    replay = parse_sse(again.text)
    assert replay[-1]["type"] == "result" and replay[-1]["message"]["id"] == first.json()["id"]
    assert len(world.runner.prompts) == 1 and len(world.db.messages) == 2

    reused = await world.client.post(url, json={**body, "content": "Other?"}, headers=key)
    assert reused.status_code == 409
    assert reused.json()["error"]["code"] == "idempotency_key_reused"
    bad_key = await world.client.post(url, json=body, headers={"Idempotency-Key": "nope"})
    assert bad_key.status_code == 422


async def test_quota_exceeded_is_429_and_keeps_nothing(world: World) -> None:
    world.ledger.caps[Bucket.ACCOUNT_QUESTIONS] = 0
    record = world.session()
    key = str(uuid.uuid4())
    response = await world.client.post(
        f"/v1/ai/sessions/{record.id}/messages",
        json={"content": "Linh Ung Pagoda hours?", "input_mode": "TEXT"},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "quota_exceeded"
    assert not world.db.messages and not world.db.idem and not world.runner.prompts


async def test_question_quota_is_checked_before_retrieval(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An over-quota question never reaches retrieval, so it spends no embedding quota."""
    calls: list[str] = []

    async def spy(self: HybridRetriever, *args: Any, **kwargs: Any) -> Any:
        calls.append("retrieve")
        raise AssertionError("retrieval must not run without question quota")

    monkeypatch.setattr(HybridRetriever, "for_city", spy)
    monkeypatch.setattr(HybridRetriever, "for_place", spy)
    world.ledger.caps[Bucket.ACCOUNT_QUESTIONS] = 0
    record = world.session()
    response = await world.client.post(
        f"/v1/ai/sessions/{record.id}/messages",
        json={"content": "Linh Ung Pagoda hours?", "input_mode": "TEXT"},
        headers=SSE,
    )
    events = parse_sse(response.text)
    assert [e.get("stage") for e in events if e["type"] == "progress"] == ["VALIDATING"]
    assert events[-1]["type"] == "error" and events[-1]["error"]["code"] == "quota_exceeded"
    assert calls == []
    assert world.ledger.used[Bucket.GEMINI_EMBED] == world.ledger.reserved[Bucket.GEMINI_EMBED] == 0
    assert sum(world.ledger.reserved.values()) == 0  # every reservation released


async def test_unexpected_failure_logs_no_question_text(
    world: World, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    async def broken(self: HybridRetriever, *args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Linh Ung Pagoda hours? secret")

    monkeypatch.setattr(HybridRetriever, "for_city", broken)
    record = world.session()
    with caplog.at_level(logging.INFO):
        response = await world.client.post(
            f"/v1/ai/sessions/{record.id}/messages",
            json={"content": "Linh Ung Pagoda hours? secret", "input_mode": "TEXT"},
            headers=SSE,
        )
    assert parse_sse(response.text)[-1]["error"]["code"] == "internal_error"
    logged = "\n".join(r.getMessage() for r in caplog.records) + "".join(
        str(r.exc_info) for r in caplog.records
    )
    assert "secret" not in logged and "guide_ask_failed" in logged
    assert world.ledger.used[Bucket.ACCOUNT_QUESTIONS] == 0


async def test_provider_failure_is_an_error_event_not_an_answer(world: World) -> None:
    record = world.session()
    world.script(RuntimeError("gemini down"), RuntimeError("groq down"))
    response = await world.client.post(
        f"/v1/ai/sessions/{record.id}/messages",
        json={"content": "Linh Ung Pagoda hours?", "input_mode": "TEXT"},
        headers=SSE,
    )
    events = parse_sse(response.text)
    assert events[-1]["type"] == "error"
    assert events[-1]["error"]["code"] == "ai_unavailable" and events[-1]["error"]["retryable"]
    assert not world.db.messages  # the traveler message is rolled back for a clean retry


async def test_question_is_redacted_before_the_model(world: World) -> None:
    record = world.session()
    world.script(answer(("Opens at 06:00.", ["E1"])))
    await world.client.post(
        f"/v1/ai/sessions/{record.id}/messages",
        json={
            "content": "Linh Ung Pagoda hours? mail me at a.b@example.com or 0905 123 456",
            "input_mode": "TEXT",
        },
    )
    prompt = world.runner.prompts[0]
    assert "a.b@example.com" not in prompt and "0905 123 456" not in prompt

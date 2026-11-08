"""Persistence seam of the Guide service (one store per unit of work)."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol

from app.guide.retrieval import EvidenceSource
from app.models.planning import IdempotencyRecord
from app.schemas.guide import Citation, GuideMessage


@dataclass(frozen=True, slots=True)
class CityRef:
    id: uuid.UUID
    code: str


@dataclass(frozen=True, slots=True)
class SessionRecord:
    id: uuid.UUID
    account_id: uuid.UUID
    trip_id: uuid.UUID | None
    place_id: uuid.UUID | None
    locale: str
    expires_at: datetime
    created_at: datetime

    @property
    def scope(self) -> str:
        return "PLACE" if self.place_id is not None else "CITY"


@dataclass(frozen=True, slots=True)
class CitationRow:
    source_revision_id: uuid.UUID
    knowledge_chunk_id: uuid.UUID | None
    place_fact_id: uuid.UUID | None


class GuideStore(EvidenceSource, Protocol):
    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    # reference
    async def enabled_city(self, code: str) -> CityRef | None: ...

    async def city(self, city_id: uuid.UUID) -> CityRef | None: ...

    async def published_place_city(self, place_id: uuid.UUID) -> uuid.UUID | None: ...

    async def owned_trip_city(
        self, trip_id: uuid.UUID, account_id: uuid.UUID
    ) -> uuid.UUID | None: ...

    # sessions
    async def insert_session(
        self,
        *,
        account_id: uuid.UUID,
        trip_id: uuid.UUID | None,
        place_id: uuid.UUID | None,
        locale: str,
        expires_at: datetime,
    ) -> SessionRecord: ...

    async def get_session(
        self, session_id: uuid.UUID, account_id: uuid.UUID, *, lock: bool = False
    ) -> SessionRecord | None: ...

    async def delete_session(self, session_id: uuid.UUID) -> None: ...

    # messages
    async def next_seq(self, session_id: uuid.UUID) -> int: ...

    async def add_message(
        self,
        *,
        session_id: uuid.UUID,
        seq: int,
        role: str,
        input_mode: str | None,
        content: str,
        answer_status: str | None,
        citations: Sequence[CitationRow] = (),
    ) -> uuid.UUID: ...

    async def delete_message(self, message_id: uuid.UUID) -> None: ...

    async def list_messages(
        self, session_id: uuid.UUID, *, after_seq: int, limit: int
    ) -> list[GuideMessage]: ...

    async def get_message(self, message_id: uuid.UUID) -> GuideMessage | None: ...

    async def recent_turns(
        self, session_id: uuid.UUID, *, before_seq: int, limit: int
    ) -> list[tuple[str, str]]: ...

    # idempotency (scope: account, GUIDE_ASK, key)
    async def claim_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        request_sha256: str,
        expires_at: datetime,
    ) -> IdempotencyRecord | None: ...

    async def complete_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        *,
        status: int,
        body: dict[str, Any],
        resource_id: uuid.UUID | None,
    ) -> None: ...

    async def release_idempotency(
        self, account_id: uuid.UUID, operation: str, key: str
    ) -> None: ...


UnitOfWork = Callable[[], AbstractAsyncContextManager[GuideStore]]


def citation_rows(citations: Sequence[Citation]) -> list[CitationRow]:
    return [
        CitationRow(c.source_revision_id, c.knowledge_chunk_id, c.place_fact_id) for c in citations
    ]

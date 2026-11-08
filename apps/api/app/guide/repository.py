"""PostgreSQL implementation of :class:`app.guide.store.GuideStore`.

Evidence reads only published content: facts pinned by a current ``PUBLISHED`` publication
(``vw_published_place_facts``) and ``APPROVED`` chunks of the corpus revision that publication
pins (the ``vw_guide_chunks`` predicate), plus approved city-scope chunks. Evidence without a
captured source revision cannot be cited and is skipped.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.guide.evidence import FACT_LABELS, Evidence, PlaceName, fact_text
from app.guide.store import CitationRow, CityRef, GuideStore, SessionRecord, UnitOfWork
from app.models.guide import GuideMessage as GuideMessageRow
from app.models.guide import GuideMessageCitation, GuideSession
from app.models.planning import IdempotencyRecord, Trip
from app.models.reference import City
from app.schemas.guide import Citation, GuideMessage
from app.trips.repository import SQLAlchemyTripStore

_FACT_FIELDS = sorted(FACT_LABELS)

# Approved chunks the Guide may cite: place chunks of the corpus revision pinned by the current
# publication (same predicate as vw_guide_chunks) and approved city-scope chunks.
_ELIGIBLE_CHUNKS = """
eligible AS (
    SELECT kc.id, kc.place_id, kc.city_id, kc.locale, kc.section, kc.content, kc.created_at,
           kc.embedding, kc.embedding_model
      FROM knowledge_chunks kc
      LEFT JOIN catalog_publications cp
        ON cp.place_id = kc.place_id AND cp.state = 'PUBLISHED'
       AND cp.corpus_revision = kc.corpus_revision
     WHERE kc.review_state = 'APPROVED'
       AND (cp.id IS NOT NULL OR (kc.scope = 'CITY' AND kc.place_id IS NULL))
)"""

_CHUNK_COLUMNS = """
       e.id AS chunk_id, e.place_id, e.locale, e.section, e.content, e.created_at,
       vw.name_vi, vw.name_en, src.source_revision_id, src.publisher, src.title, src.locator"""

_CHUNK_JOINS = """
  LEFT JOIN vw_published_places vw ON vw.place_id = e.place_id
  JOIN LATERAL (
        SELECT sr.id AS source_revision_id, s.publisher, sr.title, sr.locator
          FROM knowledge_chunk_sources ks
          JOIN source_revisions sr ON sr.id = ks.source_revision_id
          JOIN sources s ON s.id = sr.source_id
         WHERE ks.knowledge_chunk_id = e.id
         ORDER BY sr.retrieved_at DESC, sr.id
         LIMIT 1) src ON true"""

_PLACE_CHUNKS = text(
    f"WITH {_ELIGIBLE_CHUNKS} SELECT {_CHUNK_COLUMNS} FROM eligible e {_CHUNK_JOINS}"
    " WHERE e.place_id = ANY(:place_ids) AND e.locale = ANY(:locales)"
    " ORDER BY e.place_id, e.locale, e.section, e.id"
)

_LEXICAL_CHUNKS = text(
    f"WITH {_ELIGIBLE_CHUNKS}, scored AS ("
    " SELECT e.*, (SELECT count(*) FROM unnest(CAST(:patterns AS text[])) p"
    "              WHERE lower(e.content) LIKE p) AS score"
    "   FROM eligible e"
    "  WHERE e.city_id = :city_id AND e.locale = ANY(:locales)"
    "    AND lower(e.content) LIKE ANY(CAST(:patterns AS text[])))"
    f" SELECT {_CHUNK_COLUMNS}, e.score FROM scored e {_CHUNK_JOINS}"
    " ORDER BY e.score DESC, (e.locale = :locale) DESC, e.id LIMIT :limit"
)

_EMBEDDING_MODELS = text(
    f"WITH {_ELIGIBLE_CHUNKS} SELECT DISTINCT e.embedding_model FROM eligible e"
    " WHERE e.city_id = :city_id AND e.embedding IS NOT NULL AND e.embedding_model IS NOT NULL"
)

_VECTOR_CHUNKS = text(
    f"WITH {_ELIGIBLE_CHUNKS}, near AS ("
    " SELECT e.*, e.embedding <=> CAST(:vector AS vector) AS distance"
    "   FROM eligible e"
    "  WHERE e.city_id = :city_id AND e.locale = ANY(:locales)"
    "    AND e.embedding IS NOT NULL AND e.embedding_model = :model"
    "  ORDER BY distance LIMIT :limit)"
    f" SELECT {_CHUNK_COLUMNS}, e.distance FROM near e {_CHUNK_JOINS}"
    " WHERE e.distance <= :max_distance ORDER BY e.distance, e.id"
)

_PLACE_FACTS = text(
    """
SELECT vf.place_fact_id, vf.place_id, vf.field_code, vf.value, vf.verified_at, vf.is_stale,
       vw.name_vi, vw.name_en, src.source_revision_id, src.publisher, src.title, src.locator
  FROM vw_published_place_facts vf
  JOIN vw_published_places vw ON vw.catalog_publication_id = vf.catalog_publication_id
  JOIN LATERAL (
        SELECT sr.id AS source_revision_id, s.publisher, sr.title, sr.locator
          FROM fact_evidence fe
          JOIN source_revisions sr ON sr.id = fe.source_revision_id
          JOIN sources s ON s.id = sr.source_id
         WHERE fe.place_fact_id = vf.place_fact_id
         ORDER BY sr.retrieved_at DESC, sr.id
         LIMIT 1) src ON true
 WHERE vf.place_id = ANY(:place_ids)
   AND vf.knowledge_state = 'KNOWN' AND vf.value IS NOT NULL
   AND vf.field_code = ANY(:fields)
 ORDER BY vf.place_id, vf.field_code
"""
)

_PLACE_NAMES = text(
    """
SELECT vw.place_id, vw.name_vi, vw.name_en,
       coalesce(array_agg(pa.alias) FILTER (WHERE pa.alias IS NOT NULL), '{}') AS aliases
  FROM vw_published_places vw
  LEFT JOIN place_aliases pa ON pa.place_id = vw.place_id AND pa.review_state = 'APPROVED'
 WHERE vw.city_id = :city_id
 GROUP BY vw.place_id, vw.name_vi, vw.name_en
"""
)

_PUBLISHED_PLACE_CITY = text(
    "SELECT city_id FROM vw_published_places WHERE place_id = :place_id LIMIT 1"
)

_CITATIONS = text(
    """
SELECT c.guide_message_id, c.source_revision_id, c.knowledge_chunk_id, c.place_fact_id,
       s.publisher, sr.title, sr.locator, kc.section, kc.created_at AS chunk_created_at,
       pf.verified_at AS fact_verified_at
  FROM guide_message_citations c
  JOIN source_revisions sr ON sr.id = c.source_revision_id
  JOIN sources s ON s.id = sr.source_id
  LEFT JOIN knowledge_chunks kc ON kc.id = c.knowledge_chunk_id
  LEFT JOIN place_facts pf ON pf.id = c.place_fact_id
 WHERE c.guide_message_id = ANY(:message_ids)
 ORDER BY c.guide_message_id, c.source_revision_id
"""
)


def _vector_literal(vector: Sequence[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def _label(row: Any) -> str | None:
    if row.name_vi is None:
        return None
    if row.name_en and row.name_en != row.name_vi:
        return f"{row.name_vi} ({row.name_en})"
    return str(row.name_vi)


def _chunk(row: Any) -> Evidence:
    return Evidence(
        key=f"chunk:{row.chunk_id}",
        kind="CHUNK",
        place_id=row.place_id,
        text=row.content,
        source_revision_id=row.source_revision_id,
        publisher=row.publisher,
        title=row.title,
        locator=row.locator,
        verified_at=row.created_at.date() if row.created_at else None,
        knowledge_chunk_id=row.chunk_id,
        section=row.section,
        locale=row.locale,
        label=_label(row),
    )


def _fact(row: Any) -> Evidence:
    return Evidence(
        key=f"fact:{row.place_fact_id}",
        kind="FACT",
        place_id=row.place_id,
        text=fact_text(row.field_code, row.value or {}, is_stale=bool(row.is_stale)),
        source_revision_id=row.source_revision_id,
        publisher=row.publisher,
        title=row.title,
        locator=row.locator,
        verified_at=row.verified_at.date() if row.verified_at else None,
        place_fact_id=row.place_fact_id,
        field_code=row.field_code,
        label=_label(row),
    )


def _citation(row: Any) -> Citation:
    is_chunk = row.knowledge_chunk_id is not None
    verified = row.chunk_created_at if is_chunk else row.fact_verified_at
    section = (
        row.section
        if row.section in {"OVERVIEW", "HISTORY", "HIGHLIGHTS", "VISIT_TIPS", "ETIQUETTE", "ACCESS"}
        else None
    )
    return Citation(
        source_revision_id=row.source_revision_id,
        trust_level="VERIFIED",
        evidence_kind="CHUNK" if is_chunk else "FACT",
        knowledge_chunk_id=row.knowledge_chunk_id,
        section=section if is_chunk else None,
        place_fact_id=row.place_fact_id,
        publisher=row.publisher,
        title=row.title,
        locator=row.locator,
        verified_at=verified.date() if verified else None,
    )


class SQLAlchemyGuideStore(GuideStore):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    # ---- reference ------------------------------------------------------------------------------

    async def enabled_city(self, code: str) -> CityRef | None:
        row = (
            await self.session.execute(
                select(City.id, City.code).where(City.code == code, City.is_enabled.is_(True))
            )
        ).first()
        return CityRef(row.id, row.code) if row else None

    async def city(self, city_id: uuid.UUID) -> CityRef | None:
        row = (
            await self.session.execute(select(City.id, City.code).where(City.id == city_id))
        ).first()
        return CityRef(row.id, row.code) if row else None

    async def published_place_city(self, place_id: uuid.UUID) -> uuid.UUID | None:
        value = await self.session.scalar(_PUBLISHED_PLACE_CITY, {"place_id": place_id})
        return value if isinstance(value, uuid.UUID) else None

    async def owned_trip_city(self, trip_id: uuid.UUID, account_id: uuid.UUID) -> uuid.UUID | None:
        return await self.session.scalar(
            select(Trip.city_id).where(Trip.id == trip_id, Trip.account_id == account_id)
        )

    # ---- sessions -------------------------------------------------------------------------------

    @staticmethod
    def _record(row: GuideSession) -> SessionRecord:
        return SessionRecord(
            id=row.id,
            account_id=row.account_id,
            trip_id=row.trip_id,
            place_id=row.place_id,
            locale=row.locale,
            expires_at=row.expires_at,
            created_at=row.created_at,
        )

    async def insert_session(
        self,
        *,
        account_id: uuid.UUID,
        trip_id: uuid.UUID | None,
        place_id: uuid.UUID | None,
        locale: str,
        expires_at: datetime,
    ) -> SessionRecord:
        row = GuideSession(
            account_id=account_id,
            trip_id=trip_id,
            place_id=place_id,
            locale=locale,
            expires_at=expires_at,
        )
        self.session.add(row)
        await self.session.flush()
        await self.session.refresh(row)
        return self._record(row)

    async def get_session(
        self, session_id: uuid.UUID, account_id: uuid.UUID, *, lock: bool = False
    ) -> SessionRecord | None:
        stmt = select(GuideSession).where(
            GuideSession.id == session_id, GuideSession.account_id == account_id
        )
        if lock:
            stmt = stmt.with_for_update()
        row = await self.session.scalar(stmt.execution_options(populate_existing=True))
        return self._record(row) if row is not None else None

    async def delete_session(self, session_id: uuid.UUID) -> None:
        await self.session.execute(delete(GuideSession).where(GuideSession.id == session_id))

    # ---- messages -------------------------------------------------------------------------------

    async def next_seq(self, session_id: uuid.UUID) -> int:
        current = await self.session.scalar(
            select(func.max(GuideMessageRow.seq)).where(
                GuideMessageRow.guide_session_id == session_id
            )
        )
        return int(current or 0) + 1

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
    ) -> uuid.UUID:
        row = GuideMessageRow(
            guide_session_id=session_id,
            seq=seq,
            role=role,
            input_mode=input_mode,
            content=content,
            answer_status=answer_status,
        )
        self.session.add(row)
        await self.session.flush()
        for citation in citations:
            self.session.add(
                GuideMessageCitation(
                    guide_message_id=row.id,
                    source_revision_id=citation.source_revision_id,
                    knowledge_chunk_id=citation.knowledge_chunk_id,
                    place_fact_id=citation.place_fact_id,
                )
            )
        await self.session.flush()
        return row.id

    async def delete_message(self, message_id: uuid.UUID) -> None:
        await self.session.execute(delete(GuideMessageRow).where(GuideMessageRow.id == message_id))

    async def _with_citations(self, rows: Sequence[GuideMessageRow]) -> list[GuideMessage]:
        citations: dict[uuid.UUID, list[Citation]] = {}
        ids = [row.id for row in rows if row.role == "ASSISTANT"]
        if ids:
            for hit in (await self.session.execute(_CITATIONS, {"message_ids": ids})).all():
                citations.setdefault(hit.guide_message_id, []).append(_citation(hit))
        return [
            GuideMessage.model_validate(
                {
                    "id": row.id,
                    "seq": row.seq,
                    "role": row.role,
                    "input_mode": row.input_mode,
                    "content": row.content,
                    "answer_status": row.answer_status,
                    "citations": citations.get(row.id, []),
                    "created_at": row.created_at,
                }
            )
            for row in rows
        ]

    async def list_messages(
        self, session_id: uuid.UUID, *, after_seq: int, limit: int
    ) -> list[GuideMessage]:
        rows = (
            await self.session.scalars(
                select(GuideMessageRow)
                .where(
                    GuideMessageRow.guide_session_id == session_id,
                    GuideMessageRow.seq > after_seq,
                )
                .order_by(GuideMessageRow.seq)
                .limit(limit)
            )
        ).all()
        return await self._with_citations(rows)

    async def get_message(self, message_id: uuid.UUID) -> GuideMessage | None:
        row = await self.session.get(GuideMessageRow, message_id)
        if row is None:
            return None
        await self.session.refresh(row)
        return (await self._with_citations([row]))[0]

    async def recent_turns(
        self, session_id: uuid.UUID, *, before_seq: int, limit: int
    ) -> list[tuple[str, str]]:
        rows = (
            await self.session.execute(
                select(GuideMessageRow.role, GuideMessageRow.content)
                .where(
                    GuideMessageRow.guide_session_id == session_id,
                    GuideMessageRow.seq < before_seq,
                )
                .order_by(GuideMessageRow.seq.desc())
                .limit(limit)
            )
        ).all()
        return [(str(row.role), str(row.content)) for row in reversed(rows)]

    # ---- idempotency ----------------------------------------------------------------------------

    async def claim_idempotency(
        self,
        account_id: uuid.UUID,
        operation: str,
        key: str,
        request_sha256: str,
        expires_at: datetime,
    ) -> IdempotencyRecord | None:
        return await SQLAlchemyTripStore(self.session).claim_idempotency(
            account_id, operation, key, request_sha256, expires_at
        )

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
        await SQLAlchemyTripStore(self.session).complete_idempotency(
            account_id, operation, key, status=status, body=body, resource_id=resource_id
        )

    async def release_idempotency(self, account_id: uuid.UUID, operation: str, key: str) -> None:
        await self.session.execute(
            delete(IdempotencyRecord).where(
                IdempotencyRecord.account_id == account_id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.idempotency_key == key,
                IdempotencyRecord.state == "IN_PROGRESS",
            )
        )

    # ---- evidence -------------------------------------------------------------------------------

    async def place_names(self, city_id: uuid.UUID) -> list[PlaceName]:
        rows = (await self.session.execute(_PLACE_NAMES, {"city_id": city_id})).all()
        return [
            PlaceName(
                place_id=row.place_id,
                names=tuple(dict.fromkeys([row.name_vi, row.name_en, *(row.aliases or [])])),
                display_vi=row.name_vi,
                display_en=row.name_en,
            )
            for row in rows
        ]

    async def place_evidence(
        self, place_ids: Sequence[uuid.UUID], locales: Sequence[str]
    ) -> list[Evidence]:
        if not place_ids:
            return []
        ids = list(place_ids)
        facts = (
            await self.session.execute(_PLACE_FACTS, {"place_ids": ids, "fields": _FACT_FIELDS})
        ).all()
        chunks = (
            await self.session.execute(_PLACE_CHUNKS, {"place_ids": ids, "locales": list(locales)})
        ).all()
        return [*(_fact(row) for row in facts), *(_chunk(row) for row in chunks)]

    async def lexical_chunks(
        self, city_id: uuid.UUID, patterns: Sequence[str], locales: Sequence[str], limit: int
    ) -> list[Evidence]:
        if not patterns:
            return []
        rows = (
            await self.session.execute(
                _LEXICAL_CHUNKS,
                {
                    "city_id": city_id,
                    "patterns": list(patterns),
                    "locales": list(locales),
                    "locale": locales[0] if locales else "vi",
                    "limit": limit,
                },
            )
        ).all()
        return [_chunk(row) for row in rows]

    async def embedding_models(self, city_id: uuid.UUID) -> set[str]:
        rows = (await self.session.execute(_EMBEDDING_MODELS, {"city_id": city_id})).all()
        return {str(row.embedding_model) for row in rows}

    async def vector_chunks(
        self,
        city_id: uuid.UUID,
        vector: Sequence[float],
        model: str,
        locales: Sequence[str],
        limit: int,
        max_distance: float,
    ) -> list[Evidence]:
        rows = (
            await self.session.execute(
                _VECTOR_CHUNKS,
                {
                    "city_id": city_id,
                    "vector": _vector_literal(vector),
                    "model": model,
                    "locales": list(locales),
                    "limit": limit,
                    "max_distance": max_distance,
                },
            )
        ).all()
        return [_chunk(row) for row in rows]


def sql_unit_of_work(session_factory: async_sessionmaker[AsyncSession]) -> UnitOfWork:
    @asynccontextmanager
    async def open_store() -> AsyncIterator[GuideStore]:
        async with session_factory() as session:
            yield SQLAlchemyGuideStore(session)

    return open_store

"""Guide corpus chunks of a place (ADR-010, ADR-012): one chunk per section and locale.

Corpus revisions: a publication pins the place's latest approved ``corpus_revision``
(``fn_publish_place``) and ``vw_guide_chunks`` serves exactly that revision. A pinned revision
is therefore frozen: the first edit after a publication opens revision ``M + 1`` and carries
the non-retired chunks of ``M`` forward (content, sources, embedding, review state), so the
working revision is always a complete snapshot. Unpinned revisions are edited in place.

Embeddings are computed on write. Identical content (same SHA-256) reuses a stored vector of
the same place; otherwise :class:`ChunkEmbedder` is called before the place row is locked.
"""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import (
    audit,
    bump_content_revision,
    commit,
    flush,
    get_place,
    require_source_revisions,
)
from app.curation.embedding import ChunkEmbedder, Embedding
from app.errors import conflict, invalid, not_found
from app.models.catalog import CatalogPublication, Place
from app.models.knowledge import KnowledgeChunk as KnowledgeChunkRow
from app.models.knowledge import KnowledgeChunkSource
from app.schemas.admin import (
    ChunkInput,
    ChunkSaveResult,
    ChunkUpdate,
    KnowledgeChunk,
    KnowledgeChunkList,
    ReviewWarning,
)

PLACE_SECTIONS: tuple[str, ...] = (
    "OVERVIEW",
    "HISTORY",
    "HIGHLIGHTS",
    "VISIT_TIPS",
    "ETIQUETTE",
    "ACCESS",
)


def content_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def chunk_index(section: str) -> int:
    return PLACE_SECTIONS.index(section)


@dataclass
class _Working:
    revision: int
    carried: dict[uuid.UUID, uuid.UUID] = field(default_factory=dict)


@dataclass
class _Prepared:
    sha: str
    embedding: Embedding | None


class ChunkService:
    def __init__(self, session: AsyncSession, embedder: ChunkEmbedder) -> None:
        self._session = session
        self._embedder = embedder

    # ---- reads --------------------------------------------------------------------------

    async def list_chunks(
        self, place_id: uuid.UUID, *, corpus_revision: int | None = None
    ) -> KnowledgeChunkList:
        await get_place(self._session, place_id)
        latest = await self._max_revision(place_id)
        revision = corpus_revision if corpus_revision is not None else latest
        items: list[KnowledgeChunk] = []
        if revision is not None:
            rows = (
                await self._session.scalars(
                    select(KnowledgeChunkRow)
                    .where(
                        KnowledgeChunkRow.place_id == place_id,
                        KnowledgeChunkRow.corpus_revision == revision,
                    )
                    .order_by(KnowledgeChunkRow.locale, KnowledgeChunkRow.chunk_index)
                )
            ).all()
            items = await self.to_schema_many(rows)
        published = await self._session.scalar(
            select(CatalogPublication.corpus_revision).where(
                CatalogPublication.place_id == place_id, CatalogPublication.state == "PUBLISHED"
            )
        )
        return KnowledgeChunkList(
            corpus_revision=latest, published_corpus_revision=published, items=items
        )

    async def to_schema_many(self, rows: Sequence[KnowledgeChunkRow]) -> list[KnowledgeChunk]:
        ids = [row.id for row in rows]
        sources: dict[uuid.UUID, list[uuid.UUID]] = {chunk_id: [] for chunk_id in ids}
        if ids:
            links = (
                await self._session.execute(
                    select(
                        KnowledgeChunkSource.knowledge_chunk_id,
                        KnowledgeChunkSource.source_revision_id,
                    ).where(KnowledgeChunkSource.knowledge_chunk_id.in_(ids))
                )
            ).all()
            for chunk_id, source_revision_id in links:
                sources[chunk_id].append(source_revision_id)
        return [_to_schema(row, sorted(sources[row.id], key=str)) for row in rows]

    # ---- writes -------------------------------------------------------------------------

    async def save_chunk(
        self, place_id: uuid.UUID, data: ChunkInput, actor_account_id: uuid.UUID
    ) -> ChunkSaveResult:
        """Create or replace the chunk of ``(locale, section)`` in the working revision."""
        warnings: list[ReviewWarning] = []
        row = await self.apply_input(place_id, data, actor_account_id, warnings)
        await bump_content_revision(self._session, place_id)
        await commit(self._session)
        return await self._result(row, warnings)

    async def apply_input(
        self,
        place_id: uuid.UUID,
        data: ChunkInput,
        actor_account_id: uuid.UUID,
        warnings: list[ReviewWarning],
    ) -> KnowledgeChunkRow:
        """Upsert without committing (shared with the candidate review PATCH)."""
        await require_source_revisions(self._session, data.source_revision_ids)
        prepared = await self._prepare(place_id, data.content)
        place = await get_place(self._session, place_id, lock=True)
        working = await self._working_revision(place)
        row = await self._session.scalar(
            select(KnowledgeChunkRow).where(
                KnowledgeChunkRow.place_id == place_id,
                KnowledgeChunkRow.corpus_revision == working.revision,
                KnowledgeChunkRow.locale == data.locale,
                KnowledgeChunkRow.section == data.section,
            )
        )
        operation = "update" if row is not None else "create"
        if row is None:
            row = KnowledgeChunkRow(
                city_id=place.city_id,
                place_id=place.id,
                scope="PLACE",
                locale=data.locale,
                section=data.section,
                corpus_revision=working.revision,
                chunk_index=chunk_index(data.section),
                review_state="DRAFT",
            )
            self._session.add(row)
        self._apply_content(row, data.content, prepared)
        if row.review_state == "RETIRED":
            row.review_state, row.retired_at = "DRAFT", None
        await flush(self._session)
        await self._replace_sources(row.id, data.source_revision_ids)
        self._apply_requested_state(row, data.review_state, warnings, strict=False)
        if row.embedding is None:
            warnings.append(
                ReviewWarning(code="CHUNK_EMBEDDING_PENDING", knowledge_chunk_id=row.id)
            )
        await flush(self._session)
        self._audit(actor_account_id, row, operation)
        return row

    async def update_chunk(
        self,
        place_id: uuid.UUID,
        chunk_id: uuid.UUID,
        data: ChunkUpdate,
        actor_account_id: uuid.UUID,
    ) -> ChunkSaveResult:
        warnings: list[ReviewWarning] = []
        current = await self._session.scalar(
            select(KnowledgeChunkRow).where(
                KnowledgeChunkRow.id == chunk_id, KnowledgeChunkRow.place_id == place_id
            )
        )
        if current is None:
            raise not_found("Chunk not found", code="not_found")
        if data.source_revision_ids is not None:
            await require_source_revisions(self._session, data.source_revision_ids)
        prepared = await self._prepare(place_id, data.content) if data.content is not None else None
        place = await get_place(self._session, place_id, lock=True)
        working = await self._working_revision(place)
        target_id = working.carried.get(current.id, current.id)
        row = await self._session.get(KnowledgeChunkRow, target_id)
        if row is None or row.corpus_revision != working.revision:
            raise conflict(
                "chunk_not_current",
                "Only chunks of the working corpus revision can be edited",
                corpus_revision=working.revision,
            )
        if data.content is not None and prepared is not None:
            self._apply_content(row, data.content, prepared)
        if data.source_revision_ids is not None:
            await flush(self._session)
            await self._replace_sources(row.id, data.source_revision_ids)
        if data.review_state is not None:
            if data.review_state == "APPROVED" and row.embedding is None:
                embedding = await self._embedder.embed(row.content)
                if embedding is not None:
                    row.embedding, row.embedding_model = embedding.vector, embedding.model
            self._apply_requested_state(row, data.review_state, warnings, strict=True)
        if row.embedding is None:
            warnings.append(
                ReviewWarning(code="CHUNK_EMBEDDING_PENDING", knowledge_chunk_id=row.id)
            )
        await flush(self._session)
        self._audit(actor_account_id, row, "update")
        await bump_content_revision(self._session, place_id)
        await commit(self._session)
        return await self._result(row, warnings)

    # ---- internals ----------------------------------------------------------------------

    async def _prepare(self, place_id: uuid.UUID, content: str) -> _Prepared:
        sha = content_sha256(content)
        reuse = (
            await self._session.execute(
                select(KnowledgeChunkRow.embedding, KnowledgeChunkRow.embedding_model)
                .where(
                    KnowledgeChunkRow.place_id == place_id,
                    KnowledgeChunkRow.content_sha256 == sha,
                    KnowledgeChunkRow.embedding.is_not(None),
                    KnowledgeChunkRow.embedding_model.is_not(None),
                )
                .limit(1)
            )
        ).first()
        if reuse is not None:
            vector = [float(value) for value in reuse[0]]
            return _Prepared(sha, Embedding(vector=vector, model=str(reuse[1])))
        return _Prepared(sha, await self._embedder.embed(content))

    @staticmethod
    def _apply_content(row: KnowledgeChunkRow, content: str, prepared: _Prepared) -> None:
        if row.content_sha256 == prepared.sha and row.content == content:
            return
        row.content = content
        row.content_sha256 = prepared.sha
        if prepared.embedding is not None:
            row.embedding, row.embedding_model = prepared.embedding.vector, prepared.embedding.model
        else:
            row.embedding, row.embedding_model = None, None
        if row.review_state == "APPROVED":
            row.review_state = "DRAFT"  # changed text needs a fresh approval

    @staticmethod
    def _apply_requested_state(
        row: KnowledgeChunkRow, requested: str, warnings: list[ReviewWarning], *, strict: bool
    ) -> None:
        if requested == "APPROVED":
            if row.embedding is None or row.embedding_model is None:
                if strict:
                    raise invalid(
                        "chunk_embedding_pending",
                        "A chunk cannot be approved until it is embedded",
                        knowledge_chunk_id=str(row.id),
                    )
                warnings.append(
                    ReviewWarning(code="CHUNK_APPROVAL_DEFERRED", knowledge_chunk_id=row.id)
                )
                return
            row.review_state, row.retired_at = "APPROVED", None
        elif requested == "RETIRED":
            if row.review_state != "RETIRED":
                row.review_state, row.retired_at = "RETIRED", datetime.now(UTC)
        else:
            row.review_state, row.retired_at = "DRAFT", None

    async def _replace_sources(
        self, chunk_id: uuid.UUID, source_revision_ids: Sequence[uuid.UUID]
    ) -> None:
        await self._session.execute(
            delete(KnowledgeChunkSource).where(KnowledgeChunkSource.knowledge_chunk_id == chunk_id)
        )
        for source_revision_id in dict.fromkeys(source_revision_ids):
            self._session.add(
                KnowledgeChunkSource(
                    knowledge_chunk_id=chunk_id, source_revision_id=source_revision_id
                )
            )

    async def _max_revision(self, place_id: uuid.UUID) -> int | None:
        value: int | None = await self._session.scalar(
            select(func.max(KnowledgeChunkRow.corpus_revision)).where(
                KnowledgeChunkRow.place_id == place_id
            )
        )
        return value

    async def _working_revision(self, place: Place) -> _Working:
        latest = await self._max_revision(place.id)
        if latest is None:
            return _Working(revision=1)
        pinned = await self._session.scalar(
            select(func.count())
            .select_from(CatalogPublication)
            .where(
                CatalogPublication.place_id == place.id,
                CatalogPublication.corpus_revision == latest,
            )
        )
        if not pinned:
            return _Working(revision=latest)
        return await self._carry_forward(place, latest)

    async def _carry_forward(self, place: Place, pinned_revision: int) -> _Working:
        working = _Working(revision=pinned_revision + 1)
        rows = (
            await self._session.scalars(
                select(KnowledgeChunkRow).where(
                    KnowledgeChunkRow.place_id == place.id,
                    KnowledgeChunkRow.corpus_revision == pinned_revision,
                    KnowledgeChunkRow.review_state != "RETIRED",
                )
            )
        ).all()
        copies: list[tuple[KnowledgeChunkRow, KnowledgeChunkRow]] = []
        for row in rows:
            copy = KnowledgeChunkRow(
                city_id=row.city_id,
                place_id=row.place_id,
                scope=row.scope,
                locale=row.locale,
                section=row.section,
                corpus_revision=working.revision,
                chunk_index=row.chunk_index,
                content=row.content,
                content_sha256=row.content_sha256,
                embedding=row.embedding,
                embedding_model=row.embedding_model,
                review_state=row.review_state,
            )
            self._session.add(copy)
            copies.append((row, copy))
        await flush(self._session)
        for original, copy in copies:
            working.carried[original.id] = copy.id
            source_ids = (
                await self._session.scalars(
                    select(KnowledgeChunkSource.source_revision_id).where(
                        KnowledgeChunkSource.knowledge_chunk_id == original.id
                    )
                )
            ).all()
            for source_revision_id in source_ids:
                self._session.add(
                    KnowledgeChunkSource(
                        knowledge_chunk_id=copy.id, source_revision_id=source_revision_id
                    )
                )
        await flush(self._session)
        return working

    def _audit(self, actor_account_id: uuid.UUID, row: KnowledgeChunkRow, operation: str) -> None:
        detail: dict[str, Any] = {
            "operation": operation,
            "place_id": str(row.place_id),
            "locale": row.locale,
            "section": row.section,
            "corpus_revision": row.corpus_revision,
            "embedding_state": "EMBEDDED" if row.embedding is not None else "PENDING",
        }
        audit(
            self._session,
            actor_account_id=actor_account_id,
            entity_table="knowledge_chunks",
            entity_id=row.id,
            action="CONTENT_REVIEW",
            to_state=row.review_state,
            detail=detail,
        )

    async def _result(
        self, row: KnowledgeChunkRow, warnings: list[ReviewWarning]
    ) -> ChunkSaveResult:
        await self._session.refresh(row)
        [schema] = await self.to_schema_many([row])
        return ChunkSaveResult(**schema.model_dump(), warnings=warnings)


def _to_schema(row: KnowledgeChunkRow, source_revision_ids: list[uuid.UUID]) -> KnowledgeChunk:
    embedded = row.embedding is not None and row.embedding_model is not None
    return KnowledgeChunk(
        id=row.id,
        place_id=row.place_id,
        locale=row.locale,
        section=row.section,
        corpus_revision=row.corpus_revision,
        chunk_index=row.chunk_index,
        content=row.content,
        content_sha256=row.content_sha256,
        source_revision_ids=source_revision_ids,
        review_state=row.review_state,
        embedding_state="EMBEDDED" if embedded else "PENDING",
        embedding_model=row.embedding_model,
        retired_at=row.retired_at,
        created_at=row.created_at,
    )

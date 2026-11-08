"""City-level Guide chunks (ADR-010 CITY scope, DEC-032): staged by importers, approved here.

An importer (``ingest wikivoyage``) stages human-written city sections ("Understand", "Get
around", "Stay safe" …) as DRAFT ``knowledge_chunks`` (scope CITY, no place) of a new corpus
revision whenever the set of texts changes, each with its ``knowledge_chunk_sources`` row.
``publish_city_chunks`` (run by ``publish auto``) embeds the newest DRAFT revision; when every
chunk has a vector and every source is licensed and attributed, the revision is APPROVED and the
previous APPROVED city chunks are RETIRED. Otherwise the old corpus stays live (pending count).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.chunks import content_sha256
from app.curation.embedding import ChunkEmbedder
from app.models.catalog import Source, SourceRevision
from app.models.knowledge import KnowledgeChunk, KnowledgeChunkSource

CITY_SECTIONS = frozenset({"CITY_OVERVIEW", "GETTING_AROUND", "EVENTS_CALENDAR", "PRACTICAL"})
_UNUSABLE = frozenset({"", "UNKNOWN", "NONE"})


@dataclass(frozen=True)
class CityChunk:
    locale: str
    section: str
    content: str
    source_revision_id: uuid.UUID


@dataclass
class CityChunkReport:
    staged_revision: int | None = None
    approved: int = 0
    pending: int = 0
    unlicensed: int = 0
    unchanged: bool = False


def _key(locale: str, section: str, content: str) -> tuple[str, str, str]:
    return (locale, section, content_sha256(content))


async def _revision_rows(
    session: AsyncSession, city_id: uuid.UUID, revision: int
) -> list[KnowledgeChunk]:
    return list(
        (
            await session.scalars(
                select(KnowledgeChunk)
                .where(
                    KnowledgeChunk.city_id == city_id,
                    KnowledgeChunk.scope == "CITY",
                    KnowledgeChunk.corpus_revision == revision,
                )
                .order_by(KnowledgeChunk.locale, KnowledgeChunk.chunk_index)
            )
        ).all()
    )


async def stage_city_chunks(
    session: AsyncSession, city_id: uuid.UUID, chunks: Sequence[CityChunk]
) -> CityChunkReport:
    """Stage ``chunks`` as a new DRAFT corpus revision unless the newest revision has the same
    texts. Does not commit."""
    report = CityChunkReport()
    for chunk in chunks:
        if chunk.section not in CITY_SECTIONS:
            raise ValueError(f"not a city section: {chunk.section}")
    latest = await session.scalar(
        select(func.max(KnowledgeChunk.corpus_revision)).where(
            KnowledgeChunk.city_id == city_id,
            KnowledgeChunk.scope == "CITY",
            KnowledgeChunk.review_state != "RETIRED",
        )
    )
    wanted = {_key(c.locale, c.section, c.content) for c in chunks}
    if latest is not None:
        current = {
            (row.locale, row.section, row.content_sha256)
            for row in await _revision_rows(session, city_id, latest)
        }
        if current == wanted:
            report.unchanged = True
            report.staged_revision = latest
            return report
    revision = (
        await session.scalar(
            select(func.max(KnowledgeChunk.corpus_revision)).where(
                KnowledgeChunk.city_id == city_id, KnowledgeChunk.scope == "CITY"
            )
        )
        or 0
    ) + 1
    # Older DRAFT revisions that were never approved are superseded by this one.
    for row in (
        await session.scalars(
            select(KnowledgeChunk).where(
                KnowledgeChunk.city_id == city_id,
                KnowledgeChunk.scope == "CITY",
                KnowledgeChunk.review_state == "DRAFT",
            )
        )
    ).all():
        row.review_state = "RETIRED"
        row.retired_at = datetime.now(UTC)
    next_index: dict[str, int] = {}
    for chunk in chunks:
        index = next_index.get(chunk.locale, 0)
        next_index[chunk.locale] = index + 1
        row = KnowledgeChunk(
            city_id=city_id,
            place_id=None,
            scope="CITY",
            locale=chunk.locale,
            section=chunk.section,
            corpus_revision=revision,
            chunk_index=index,
            content=chunk.content,
            content_sha256=content_sha256(chunk.content),
            review_state="DRAFT",
        )
        session.add(row)
        await session.flush()
        session.add(
            KnowledgeChunkSource(
                knowledge_chunk_id=row.id, source_revision_id=chunk.source_revision_id
            )
        )
    await session.flush()
    report.staged_revision = revision
    return report


async def publish_city_chunks(
    session: AsyncSession, *, city_id: uuid.UUID, embedder: ChunkEmbedder, dry_run: bool = False
) -> CityChunkReport:
    report = CityChunkReport()
    revision = await session.scalar(
        select(func.max(KnowledgeChunk.corpus_revision)).where(
            KnowledgeChunk.city_id == city_id,
            KnowledgeChunk.scope == "CITY",
            KnowledgeChunk.review_state == "DRAFT",
        )
    )
    if revision is None:
        report.unchanged = True
        return report
    report.staged_revision = revision
    rows = [
        r for r in await _revision_rows(session, city_id, revision) if r.review_state == "DRAFT"
    ]
    licences = (
        await session.execute(
            select(
                KnowledgeChunkSource.knowledge_chunk_id,
                Source.license_code,
                Source.attribution_text,
            )
            .join(SourceRevision, SourceRevision.id == KnowledgeChunkSource.source_revision_id)
            .join(Source, Source.id == SourceRevision.source_id)
            .where(KnowledgeChunkSource.knowledge_chunk_id.in_([r.id for r in rows]))
        )
    ).all()
    licensed = {
        row[0]
        for row in licences
        if str(row[1]).strip().upper() not in _UNUSABLE and (row[2] or "").strip()
    }
    report.unlicensed = sum(1 for r in rows if r.id not in licensed)
    if report.unlicensed or dry_run:
        report.pending = len(rows)
        return report
    reusable: dict[str, tuple[Any, str]] = {}
    for hit in (
        await session.execute(
            select(
                KnowledgeChunk.content_sha256,
                KnowledgeChunk.embedding,
                KnowledgeChunk.embedding_model,
            ).where(
                KnowledgeChunk.city_id == city_id,
                KnowledgeChunk.scope == "CITY",
                KnowledgeChunk.embedding.is_not(None),
            )
        )
    ).all():
        if hit[2]:
            reusable[str(hit[0])] = (hit[1], str(hit[2]))
    for row in rows:
        if row.embedding is not None:
            continue
        if row.content_sha256 in reusable:
            row.embedding, row.embedding_model = reusable[row.content_sha256]
            continue
        embedding = await embedder.embed(row.content)
        if embedding is None:
            continue
        row.embedding, row.embedding_model = embedding.vector, embedding.model
        reusable[row.content_sha256] = (embedding.vector, embedding.model)
    await session.flush()
    report.pending = sum(1 for r in rows if r.embedding is None)
    if report.pending:
        await session.commit()  # keep the vectors already paid for
        return report
    now = datetime.now(UTC)
    for old in (
        await session.scalars(
            select(KnowledgeChunk).where(
                KnowledgeChunk.city_id == city_id,
                KnowledgeChunk.scope == "CITY",
                KnowledgeChunk.review_state == "APPROVED",
            )
        )
    ).all():
        old.review_state = "RETIRED"
        old.retired_at = now
    await session.flush()
    for row in rows:
        row.review_state = "APPROVED"
    report.approved = len(rows)
    await session.commit()
    return report

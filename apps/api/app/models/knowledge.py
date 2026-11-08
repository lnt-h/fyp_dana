"""Guide corpus: sectioned knowledge chunks with pgvector embeddings (schema.sql §5)."""

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CHAR,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.constants import EMBEDDING_DIMENSIONS


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name="fk_knowledge_chunks_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["place_id", "city_id"],
            ["places.id", "places.city_id"],
            name="fk_knowledge_chunks_place_id_city_id",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "city_id",
            "place_id",
            "locale",
            "corpus_revision",
            "chunk_index",
            name="uq_knowledge_chunks_city_id_place_id_locale_corpus_revision_chu",
            postgresql_nulls_not_distinct=True,
        ),
        # Migration 0010: one section per PLACE corpus revision is the partial unique index
        # uq_knowledge_chunks_place_section (WHERE scope = 'PLACE'), managed in SQL like the
        # other indexes; CITY revisions hold several chunks per section.
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    place_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    scope: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'PLACE'"))
    locale: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[str] = mapped_column(Text, nullable=False)
    corpus_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'DRAFT'"))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class KnowledgeChunkSource(Base):
    __tablename__ = "knowledge_chunk_sources"
    __table_args__ = (
        ForeignKeyConstraint(
            ["knowledge_chunk_id"],
            ["knowledge_chunks.id"],
            name="fk_knowledge_chunk_sources_knowledge_chunk_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["source_revision_id"],
            ["source_revisions.id"],
            name="fk_knowledge_chunk_sources_source_revision_id",
            ondelete="RESTRICT",
        ),
    )

    knowledge_chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

"""Provider caches with policy-bounded TTLs (schema.sql §8A / migration 0004, ADR-006)."""

import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import CHAR, DateTime, ForeignKeyConstraint, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import Geography
from app.models.constants import EMBEDDING_DIMENSIONS


class RoutesMatrixCache(Base):
    __tablename__ = "routes_matrix_cache"
    __table_args__ = (
        ForeignKeyConstraint(
            ["provider_policy_id"],
            ["provider_policies.id"],
            name="fk_routes_matrix_cache_provider_policy_id",
            ondelete="RESTRICT",
        ),
    )

    origin_key: Mapped[str] = mapped_column(Text, primary_key=True)
    destination_key: Mapped[str] = mapped_column(Text, primary_key=True)
    travel_mode: Mapped[str] = mapped_column(Text, primary_key=True)
    availability: Mapped[str] = mapped_column(Text, nullable=False)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    provider_policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ResearchCache(Base):
    __tablename__ = "research_cache"
    __table_args__ = (
        ForeignKeyConstraint(
            ["provider_policy_id"],
            ["provider_policies.id"],
            name="fk_research_cache_provider_policy_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["source_revision_id"],
            ["source_revisions.id"],
            name="fk_research_cache_source_revision_id",
            ondelete="SET NULL",
        ),
    )

    provider: Mapped[str] = mapped_column(Text, primary_key=True)
    key_sha256: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    source_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    provider_policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PlacesLookupCache(Base):
    __tablename__ = "places_lookup_cache"
    __table_args__ = (
        ForeignKeyConstraint(
            ["provider_policy_id"],
            ["provider_policies.id"],
            name="fk_places_lookup_cache_provider_policy_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("google_place_id", name="uq_places_lookup_cache_google_place_id"),
        UniqueConstraint("query_sha256", name="uq_places_lookup_cache_query_sha256"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    query_sha256: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    google_place_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Geography("Point"), nullable=True)
    location_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    provider_policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    outcome_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QueryEmbeddingCache(Base):
    __tablename__ = "query_embedding_cache"
    __table_args__ = (
        ForeignKeyConstraint(
            ["provider_policy_id"],
            ["provider_policies.id"],
            name="fk_query_embedding_cache_provider_policy_id",
            ondelete="RESTRICT",
        ),
    )

    text_sha256: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    locale: Mapped[str] = mapped_column(Text, primary_key=True)
    embedding_model: Mapped[str] = mapped_column(Text, primary_key=True)
    embedding: Mapped[Any] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    provider_policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

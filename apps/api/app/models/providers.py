"""Providers, policies, field rules, open-data staging and external identities (schema.sql §3)."""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CHAR,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import Geography


class DataProvider(Base):
    __tablename__ = "data_providers"
    __table_args__ = (UniqueConstraint("provider_key", name="uq_data_providers_provider_key"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    provider_key: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    provider_kind: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class ProviderPolicy(Base):
    __tablename__ = "provider_policies"
    __table_args__ = (
        ForeignKeyConstraint(
            ["data_provider_id"],
            ["data_providers.id"],
            name="fk_provider_policies_data_provider_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "data_provider_id",
            "policy_revision",
            name="uq_provider_policies_data_provider_id_policy_revision",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    data_provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    policy_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    terms_version: Mapped[str] = mapped_column(Text, nullable=False)
    terms_url: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    attribution_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'DRAFT'"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_review_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class ProviderFieldRule(Base):
    __tablename__ = "provider_field_rules"
    __table_args__ = (
        ForeignKeyConstraint(
            ["provider_policy_id"],
            ["provider_policies.id"],
            name="fk_provider_field_rules_provider_policy_id",
            ondelete="CASCADE",
        ),
    )

    provider_policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    field_name: Mapped[str] = mapped_column(Text, primary_key=True)
    persistence_class: Mapped[str] = mapped_column(Text, nullable=False)
    max_retention: Mapped[timedelta | None] = mapped_column(INTERVAL, nullable=True)


class ImportRun(Base):
    __tablename__ = "import_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name="fk_import_runs_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["data_provider_id"],
            ["data_providers.id"],
            name="fk_import_runs_data_provider_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["provider_policy_id"],
            ["provider_policies.id"],
            name="fk_import_runs_provider_policy_id",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    data_provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider_policy_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    release_id: Mapped[str] = mapped_column(Text, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    importer_version: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'RUNNING'"))
    record_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accepted_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rejected_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duplicate_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ImportRecord(Base):
    __tablename__ = "import_records"
    __table_args__ = (
        ForeignKeyConstraint(
            ["import_run_id"],
            ["import_runs.id"],
            name="fk_import_records_import_run_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["place_id"],
            ["places.id"],
            name="fk_import_records_place_id",
            ondelete="SET NULL",
        ),
        UniqueConstraint(
            "import_run_id", "upstream_id", name="uq_import_records_import_run_id_upstream_id"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    import_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    upstream_id: Mapped[str] = mapped_column(Text, nullable=False)
    raw_name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False)
    upstream_category: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(Geography("Point"), nullable=False)
    allowed_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    validation_status: Mapped[str] = mapped_column(Text, nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'UNMATCHED'")
    )
    place_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class ExternalPlaceIdentity(Base):
    __tablename__ = "external_place_identities"
    __table_args__ = (
        ForeignKeyConstraint(
            ["data_provider_id"],
            ["data_providers.id"],
            name="fk_external_place_identities_data_provider_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["place_id"],
            ["places.id"],
            name="fk_external_place_identities_place_id",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "data_provider_id",
            "upstream_id",
            name="uq_external_place_identities_data_provider_id_upstream_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    place_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    data_provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    upstream_id: Mapped[str] = mapped_column(Text, nullable=False)
    upstream_release: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_method: Mapped[str] = mapped_column(Text, nullable=False)
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    review_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'PENDING'")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

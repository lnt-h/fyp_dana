"""Places, reviewed content, provenance, media, web candidates, calendar rules and publications
(schema.sql §3-§4A, §6)."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Identity,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import Geography


class Place(Base):
    __tablename__ = "places"
    __table_args__ = (
        ForeignKeyConstraint(
            ["area_code", "city_id"],
            ["areas.code", "areas.city_id"],
            name="fk_places_area_code_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["category_code"],
            ["categories.code"],
            name="fk_places_category_code",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name="fk_places_city_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("city_id", "slug", name="uq_places_city_id_slug"),
        UniqueConstraint("id", "city_id", name="uq_places_id_city_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    area_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    category_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'IMPORTED'")
    )
    location: Mapped[str] = mapped_column(Geography("Point"), nullable=False)
    visit_minutes_min: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    visit_minutes_suggested: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    visit_minutes_max: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    has_no_media: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    content_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PlaceLocalization(Base):
    __tablename__ = "place_localizations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["place_id"],
            ["places.id"],
            name="fk_place_localizations_place_id",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "place_id",
            "locale",
            "localization_revision",
            name="uq_place_localizations_place_id_locale_localization_revision",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    place_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    locale: Mapped[str] = mapped_column(Text, nullable=False)
    localization_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    translation_origin: Mapped[str] = mapped_column(Text, nullable=False)
    review_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'DRAFT'"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PlaceAlias(Base):
    __tablename__ = "place_aliases"
    __table_args__ = (
        ForeignKeyConstraint(
            ["place_id"],
            ["places.id"],
            name="fk_place_aliases_place_id",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "place_id",
            "locale",
            "alias_normalized",
            name="uq_place_aliases_place_id_locale_alias_normalized",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    place_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    locale: Mapped[str] = mapped_column(Text, nullable=False)
    alias_kind: Mapped[str] = mapped_column(Text, nullable=False)
    alias: Mapped[str] = mapped_column(Text, nullable=False)
    alias_normalized: Mapped[str] = mapped_column(Text, nullable=False)
    review_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'DRAFT'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (
        ForeignKeyConstraint(
            ["data_provider_id"],
            ["data_providers.id"],
            name="fk_sources_data_provider_id",
            ondelete="SET NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    data_provider_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    publisher: Mapped[str] = mapped_column(Text, nullable=False)
    source_kind: Mapped[str] = mapped_column(Text, nullable=False)
    homepage_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    license_code: Mapped[str] = mapped_column(Text, nullable=False)
    attribution_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class SourceRevision(Base):
    __tablename__ = "source_revisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name="fk_source_revisions_source_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "source_id",
            "locator",
            "retrieved_at",
            name="uq_source_revisions_source_id_locator_retrieved_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    locator: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_sha256: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    private_evidence_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PlaceFact(Base):
    __tablename__ = "place_facts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["field_code"],
            ["fact_fields.code"],
            name="fk_place_facts_field_code",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["place_id"],
            ["places.id"],
            name="fk_place_facts_place_id",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "place_id",
            "field_code",
            "fact_revision",
            name="uq_place_facts_place_id_field_code_fact_revision",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    place_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_code: Mapped[str] = mapped_column(Text, nullable=False)
    fact_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    knowledge_state: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    review_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'DRAFT'"))
    conflict_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'NONE'"))
    conflict_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class FactEvidence(Base):
    __tablename__ = "fact_evidence"
    __table_args__ = (
        ForeignKeyConstraint(
            ["place_fact_id"],
            ["place_facts.id"],
            name="fk_fact_evidence_place_fact_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["source_revision_id"],
            ["source_revisions.id"],
            name="fk_fact_evidence_source_revision_id",
            ondelete="RESTRICT",
        ),
    )

    place_fact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    supported_claim: Mapped[str] = mapped_column(Text, nullable=False)


class MediaAsset(Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source_revision_id"],
            ["source_revisions.id"],
            name="fk_media_assets_source_revision_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("object_key", name="uq_media_assets_object_key"),
        UniqueConstraint("sha256", name="uq_media_assets_sha256"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    width_px: Mapped[int] = mapped_column(Integer, nullable=False)
    height_px: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    creator: Mapped[str] = mapped_column(Text, nullable=False)
    source_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    license_code: Mapped[str] = mapped_column(Text, nullable=False)
    attribution_text: Mapped[str] = mapped_column(Text, nullable=False)
    rights_proof_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    rights_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'PENDING'")
    )
    rights_expires_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PlaceMedia(Base):
    __tablename__ = "place_media"
    __table_args__ = (
        ForeignKeyConstraint(
            ["media_asset_id"],
            ["media_assets.id"],
            name="fk_place_media_media_asset_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["place_id"],
            ["places.id"],
            name="fk_place_media_place_id",
            ondelete="CASCADE",
        ),
        UniqueConstraint("place_id", "ordinal", name="uq_place_media_place_id_ordinal"),
    )

    place_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    media_asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    ordinal: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    alt_text_vi: Mapped[str] = mapped_column(Text, nullable=False)
    alt_text_en: Mapped[str] = mapped_column(Text, nullable=False)


class WebPlaceCandidate(Base):
    __tablename__ = "web_place_candidates"
    __table_args__ = (
        ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name="fk_web_place_candidates_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["promoted_place_id", "city_id"],
            ["places.id", "places.city_id"],
            name="fk_web_place_candidates_promoted_place_id_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["reviewed_by_account_id"],
            ["accounts.id"],
            name="fk_web_place_candidates_reviewed_by_account_id",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["source_revision_id"],
            ["source_revisions.id"],
            name="fk_web_place_candidates_source_revision_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "city_id", name="uq_web_place_candidates_id_city_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_vi: Mapped[str | None] = mapped_column(Text, nullable=True)
    name_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_guess: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(Geography("Point"), nullable=True)
    coordinate_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_place_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    places_check_outcome: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'SKIPPED'")
    )
    places_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tavily_query: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    extraction_model: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_state: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'PENDING'")
    )
    promoted_place_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reviewed_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    times_proposed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PlaceClosureRule(Base):
    __tablename__ = "place_closure_rules"
    __table_args__ = (
        ForeignKeyConstraint(
            ["area_code", "city_id"],
            ["areas.code", "areas.city_id"],
            name="fk_place_closure_rules_area_code_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name="fk_place_closure_rules_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["place_id", "city_id"],
            ["places.id", "places.city_id"],
            name="fk_place_closure_rules_place_id_city_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["reviewed_by_account_id"],
            ["accounts.id"],
            name="fk_place_closure_rules_reviewed_by_account_id",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["source_revision_id"],
            ["source_revisions.id"],
            name="fk_place_closure_rules_source_revision_id",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    applies_to: Mapped[str] = mapped_column(Text, nullable=False)
    place_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    area_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_kind: Mapped[str] = mapped_column(Text, nullable=False)
    effect: Mapped[str] = mapped_column(Text, nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    note_vi: Mapped[str] = mapped_column(Text, nullable=False)
    note_en: Mapped[str] = mapped_column(Text, nullable=False)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    review_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'DRAFT'"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class CatalogPublication(Base):
    __tablename__ = "catalog_publications"
    __table_args__ = (
        ForeignKeyConstraint(
            ["area_code", "city_id"],
            ["areas.code", "areas.city_id"],
            name="fk_catalog_publications_area_code_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["category_code"],
            ["categories.code"],
            name="fk_catalog_publications_category_code",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["localization_en_id"],
            ["place_localizations.id"],
            name="fk_catalog_publications_localization_en_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["localization_vi_id"],
            ["place_localizations.id"],
            name="fk_catalog_publications_localization_vi_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["place_id", "city_id"],
            ["places.id", "places.city_id"],
            name="fk_catalog_publications_place_id_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["published_by_account_id"],
            ["accounts.id"],
            name="fk_catalog_publications_published_by_account_id",
            ondelete="SET NULL",
        ),
        UniqueConstraint("id", "place_id", name="uq_catalog_publications_id_place_id"),
        UniqueConstraint(
            "place_id",
            "publication_revision",
            name="uq_catalog_publications_place_id_publication_revision",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    place_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    publication_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'PUBLISHED'"))
    category_code: Mapped[str] = mapped_column(Text, nullable=False)
    area_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str] = mapped_column(Geography("Point"), nullable=False)
    entrance_location: Mapped[str | None] = mapped_column(Geography("Point"), nullable=True)
    visit_minutes_min: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    visit_minutes_suggested: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    visit_minutes_max: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    localization_vi_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    localization_en_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    corpus_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    published_by_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    state_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    state_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class PublicationFact(Base):
    __tablename__ = "publication_facts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["catalog_publication_id"],
            ["catalog_publications.id"],
            name="fk_publication_facts_catalog_publication_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["place_fact_id"],
            ["place_facts.id"],
            name="fk_publication_facts_place_fact_id",
            ondelete="RESTRICT",
        ),
    )

    catalog_publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    place_fact_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)


class PublicationMedia(Base):
    __tablename__ = "publication_media"
    __table_args__ = (
        ForeignKeyConstraint(
            ["catalog_publication_id"],
            ["catalog_publications.id"],
            name="fk_publication_media_catalog_publication_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["media_asset_id"],
            ["media_assets.id"],
            name="fk_publication_media_media_asset_id",
            ondelete="RESTRICT",
        ),
    )

    catalog_publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    media_asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    ordinal: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class CatalogAuditEvent(Base):
    __tablename__ = "catalog_audit_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["actor_account_id"],
            ["accounts.id"],
            name="fk_catalog_audit_events_actor_account_id",
            ondelete="SET NULL",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    actor_account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    entity_table: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    from_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_state: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

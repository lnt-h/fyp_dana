"""Owner-scoped planning: preferences, trips, previews, idempotency, deletion (schema.sql §7)."""

import uuid
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import (
    CHAR,
    Boolean,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    SmallInteger,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AccountPreferences(Base):
    __tablename__ = "account_preferences"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_account_preferences_account_id",
            ondelete="CASCADE",
        ),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    locale: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'vi'"))
    pace: Mapped[str | None] = mapped_column(Text, nullable=True)
    interest_category_codes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    allowed_modes: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{WALK,DRIVE}'::text[]")
    )
    day_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    day_end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    ai_notice_acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_trips_account_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name="fk_trips_city_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "account_id", name="uq_trips_id_account_id"),
        UniqueConstraint("id", "city_id", name="uq_trips_id_city_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    day_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'DRAFT'"))
    revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    planning_preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    saved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class TripDay(Base):
    __tablename__ = "trip_days"
    __table_args__ = (
        ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            name="fk_trip_days_trip_id",
            ondelete="CASCADE",
        ),
        UniqueConstraint("id", "trip_id", name="uq_trip_days_id_trip_id"),
        UniqueConstraint("trip_id", "day_index", name="uq_trip_days_trip_id_day_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    day_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    day_window_start: Mapped[time] = mapped_column(Time, nullable=False)
    day_window_end: Mapped[time] = mapped_column(Time, nullable=False)


class TripStop(Base):
    __tablename__ = "trip_stops"
    __table_args__ = (
        ForeignKeyConstraint(
            ["catalog_publication_id", "place_id"],
            ["catalog_publications.id", "catalog_publications.place_id"],
            name="fk_trip_stops_catalog_publication_id_place_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["place_id", "city_id"],
            ["places.id", "places.city_id"],
            name="fk_trip_stops_place_id_city_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["trip_day_id", "trip_id"],
            ["trip_days.id", "trip_days.trip_id"],
            name="fk_trip_stops_trip_day_id_trip_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["trip_id", "city_id"],
            ["trips.id", "trips.city_id"],
            name="fk_trip_stops_trip_id_city_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["web_place_candidate_id", "city_id"],
            ["web_place_candidates.id", "web_place_candidates.city_id"],
            name="fk_trip_stops_web_place_candidate_id_city_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("id", "trip_day_id", name="uq_trip_stops_id_trip_day_id"),
        UniqueConstraint(
            "trip_day_id",
            "ordinal",
            name="uq_trip_stops_trip_day_id_ordinal",
            deferrable=True,
            initially="IMMEDIATE",
        ),
        UniqueConstraint("trip_id", "place_id", name="uq_trip_stops_trip_id_place_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    trip_day_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    trust_level: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'VERIFIED'")
    )
    place_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    catalog_publication_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    web_place_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    ordinal: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    planned_arrival: Mapped[time] = mapped_column(Time, nullable=False)
    planned_departure: Mapped[time] = mapped_column(Time, nullable=False)
    visit_minutes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))


class RouteLeg(Base):
    __tablename__ = "route_legs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["data_provider_id"],
            ["data_providers.id"],
            name="fk_route_legs_data_provider_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["from_stop_id", "trip_day_id"],
            ["trip_stops.id", "trip_stops.trip_day_id"],
            name="fk_route_legs_from_stop_id_trip_day_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["to_stop_id", "trip_day_id"],
            ["trip_stops.id", "trip_stops.trip_day_id"],
            name="fk_route_legs_to_stop_id_trip_day_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["trip_day_id"],
            ["trip_days.id"],
            name="fk_route_legs_trip_day_id",
            ondelete="CASCADE",
        ),
        UniqueConstraint("from_stop_id", name="uq_route_legs_from_stop_id"),
        UniqueConstraint("to_stop_id", name="uq_route_legs_to_stop_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    trip_day_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    from_stop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_stop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    travel_mode: Mapped[str] = mapped_column(Text, nullable=False)
    availability: Mapped[str] = mapped_column(Text, nullable=False)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_s: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_provider_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    measured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PlanPreview(Base):
    __tablename__ = "plan_previews"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_plan_previews_account_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["trip_id", "account_id"],
            ["trips.id", "trips.account_id"],
            name="fk_plan_previews_trip_id_account_id",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    trip_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    base_trip_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    head_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'ACTIVE'"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class PreviewRevision(Base):
    __tablename__ = "preview_revisions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["plan_preview_id"],
            ["plan_previews.id"],
            name="fk_preview_revisions_plan_preview_id",
            ondelete="CASCADE",
        ),
    )

    plan_preview_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    preview_revision: Mapped[int] = mapped_column(Integer, primary_key=True)
    parent_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    origin: Mapped[str] = mapped_column(Text, nullable=False)
    plan_health: Mapped[str] = mapped_column(Text, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    model_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    corpus_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_idempotency_records_account_id",
            ondelete="CASCADE",
        ),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    operation: Mapped[str] = mapped_column(Text, primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(Text, primary_key=True)
    request_sha256: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'IN_PROGRESS'"))
    response_status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AccountDeletionJob(Base):
    __tablename__ = "account_deletion_jobs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_account_deletion_jobs_account_id",
            ondelete="SET NULL",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'REQUESTED'"))
    attempt_count: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

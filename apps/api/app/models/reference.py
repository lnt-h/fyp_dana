"""Reference data: cities, travel areas, categories and the fact vocabulary (schema.sql §2)."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.types import Geography


class City(Base):
    __tablename__ = "cities"
    __table_args__ = (UniqueConstraint("code", name="uq_cities_code"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name_vi: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    time_zone: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'Asia/Ho_Chi_Minh'")
    )
    boundary: Mapped[str | None] = mapped_column(Geography("MultiPolygon"), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Area(Base):
    __tablename__ = "areas"
    __table_args__ = (
        ForeignKeyConstraint(
            ["city_id"],
            ["cities.id"],
            name="fk_areas_city_id",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("code", "city_id", name="uq_areas_code_city_id"),
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    city_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name_vi: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    boundary: Mapped[str | None] = mapped_column(Geography("MultiPolygon"), nullable=True)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class Category(Base):
    __tablename__ = "categories"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name_vi: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class FactField(Base):
    __tablename__ = "fact_fields"

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    is_operational: Mapped[bool] = mapped_column(Boolean, nullable=False)
    required_for_publication: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    value_kind: Mapped[str] = mapped_column(Text, nullable=False)
    stale_after_days: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

"""Private Guide sessions, messages and citations (schema.sql §7)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Integer, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GuideSession(Base):
    __tablename__ = "guide_sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_guide_sessions_account_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["place_id"],
            ["places.id"],
            name="fk_guide_sessions_place_id",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["trip_id", "account_id"],
            ["trips.id", "trips.account_id"],
            name="fk_guide_sessions_trip_id_account_id",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    trip_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    place_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    locale: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class GuideMessage(Base):
    __tablename__ = "guide_messages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["guide_session_id"],
            ["guide_sessions.id"],
            name="fk_guide_messages_guide_session_id",
            ondelete="CASCADE",
        ),
        UniqueConstraint("guide_session_id", "seq", name="uq_guide_messages_guide_session_id_seq"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    guide_session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    input_mode: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    answer_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class GuideMessageCitation(Base):
    __tablename__ = "guide_message_citations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["guide_message_id"],
            ["guide_messages.id"],
            name="fk_guide_message_citations_guide_message_id",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["knowledge_chunk_id"],
            ["knowledge_chunks.id"],
            name="fk_guide_message_citations_knowledge_chunk_id",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["place_fact_id"],
            ["place_facts.id"],
            name="fk_guide_message_citations_place_fact_id",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["source_revision_id"],
            ["source_revisions.id"],
            name="fk_guide_message_citations_source_revision_id",
            ondelete="RESTRICT",
        ),
    )

    guide_message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    source_revision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    knowledge_chunk_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    place_fact_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

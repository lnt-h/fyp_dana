"""User-study records (schema.sql §8, migration 0005)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StudyParticipant(Base):
    __tablename__ = "study_participants"
    __table_args__ = (
        ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name="fk_study_participants_account_id",
            ondelete="SET NULL",
        ),
        UniqueConstraint("account_id", name="uq_study_participants_account_id"),
        UniqueConstraint("participant_code", name="uq_study_participants_participant_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    participant_code: Mapped[str] = mapped_column(Text, nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StudySessionLog(Base):
    __tablename__ = "study_session_logs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["study_participant_id"],
            ["study_participants.id"],
            name="fk_study_session_logs_study_participant_id",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    study_participant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    interface_locale: Mapped[str] = mapped_column(Text, nullable=False)
    request_submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_proposal_displayed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    save_outcome: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

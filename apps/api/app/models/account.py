from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "accounts"

    # Uniqueness is the constraint accounts_clerk_user_id_key; the duplicate unique index
    # ix_accounts_clerk_user_id was dropped in migration 0002 (OQ-020).
    clerk_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

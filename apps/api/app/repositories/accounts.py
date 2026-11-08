import hashlib
from typing import Protocol

from sqlalchemy import exists, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import DEMO_SHARED_SUBJECT
from app.models.account import Account
from app.models.planning import AccountDeletionJob


class DeletedSubjectError(Exception):
    """The Clerk subject belongs to an account whose deletion job COMPLETED (BR-021)."""


def subject_sha256(clerk_user_id: str) -> str:
    """Hex SHA-256 of a Clerk subject, stored on deletion jobs instead of the subject itself."""
    return hashlib.sha256(clerk_user_id.encode("utf-8")).hexdigest()


class AccountRepository(Protocol):
    async def get_or_create(self, clerk_user_id: str) -> Account: ...


class SQLAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, clerk_user_id: str) -> Account:
        """Map a Clerk subject to its account, creating it on first sight.

        Raises :class:`DeletedSubjectError` instead of re-creating an account for a subject whose
        deletion completed (``account_deletion_jobs.clerk_subject_sha256``, partial index on
        COMPLETED), so a still-valid token of a purged user cannot start a fresh account.
        """
        existing = await self._session.scalar(
            select(Account).where(Account.clerk_user_id == clerk_user_id)
        )
        if existing is not None:
            return existing

        # The shared demo subject (owner demo builds only) is never locked out: deleting the
        # demo account purges it and the next demo request starts a fresh one.
        deleted = clerk_user_id != DEMO_SHARED_SUBJECT and await self._session.scalar(
            select(
                exists().where(
                    AccountDeletionJob.status == "COMPLETED",
                    AccountDeletionJob.clerk_subject_sha256 == subject_sha256(clerk_user_id),
                )
            )
        )
        if deleted:
            raise DeletedSubjectError

        statement = (
            insert(Account)
            .values(clerk_user_id=clerk_user_id)
            .on_conflict_do_nothing(index_elements=[Account.clerk_user_id])
            .returning(Account)
        )
        inserted = (await self._session.execute(statement)).scalar_one_or_none()
        if inserted is not None:
            await self._session.commit()
            return inserted

        existing = await self._session.scalar(
            select(Account).where(Account.clerk_user_id == clerk_user_id)
        )
        if existing is None:
            raise RuntimeError("Account mapping disappeared during authentication")
        return existing

"""Curator role check for ``/v1/admin`` (architecture §6, CMP-006).

A curator is a Clerk user whose subject is listed in ``GONARRA_CURATOR_CLERK_USER_IDS``. The
check runs before any database access; a signed-in non-curator gets 403
``curator_role_required``. The account row is resolved only after the role check, and a curator
whose account has an open deletion job gets 409 ``deletion_in_progress`` like every other route.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.errors import AppError
from app.models.account import Account
from app.models.planning import AccountDeletionJob
from app.repositories.accounts import DeletedSubjectError, SQLAlchemyAccountRepository
from app.security.clerk import (
    OPEN_DELETION_STATUSES,
    AuthenticatedUser,
    deletion_in_progress,
    get_current_user,
    has_open_deletion_job,
)


def is_curator(user: AuthenticatedUser, settings: Settings) -> bool:
    return user.subject in settings.curator_subjects


async def require_curator(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser:
    if not is_curator(user, settings):
        raise AppError(403, "curator_role_required", "Curator role required")
    return user


async def get_curator_account(
    user: Annotated[AuthenticatedUser, Depends(require_curator)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Account:
    try:
        account = await SQLAlchemyAccountRepository(session).get_or_create(user.subject)
    except DeletedSubjectError as exc:
        raise AppError(401, "authentication_required", "Invalid session token") from exc
    if await has_open_deletion_job(session, account.id):
        raise deletion_in_progress()
    return account


async def require_active_curator(
    user: Annotated[AuthenticatedUser, Depends(require_curator)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthenticatedUser:
    """``require_curator`` plus the deletion guard for routes that never resolve the account.

    One lookup by subject (accounts unique key → open-job partial index). Intended as the
    ``/v1/admin`` router-level dependency in place of ``require_curator``.
    """
    statement = select(
        exists()
        .where(Account.clerk_user_id == user.subject)
        .where(AccountDeletionJob.account_id == Account.id)
        .where(AccountDeletionJob.status.in_(OPEN_DELETION_STATUSES))
    )
    if await session.scalar(statement):
        raise deletion_in_progress()
    return user

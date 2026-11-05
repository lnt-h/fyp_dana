"""Curator role check for ``/v1/admin`` (architecture §6, CMP-006).

A curator is a Clerk user whose subject is listed in ``GONARRA_CURATOR_CLERK_USER_IDS``. The
check runs before any database access; a signed-in non-curator gets 403
``curator_role_required``. The account row is resolved only after the role check.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.errors import ApiError
from app.models.account import Account
from app.repositories.accounts import SQLAlchemyAccountRepository
from app.security.clerk import AuthenticatedUser, get_current_user


def is_curator(user: AuthenticatedUser, settings: Settings) -> bool:
    return user.subject in settings.curator_subjects


async def require_curator(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser:
    if not is_curator(user, settings):
        raise ApiError(403, "curator_role_required", "Curator role required")
    return user


async def get_curator_account(
    user: Annotated[AuthenticatedUser, Depends(require_curator)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Account:
    return await SQLAlchemyAccountRepository(session).get_or_create(user.subject)

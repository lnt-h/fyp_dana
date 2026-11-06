"""The automated pipeline's reviewer identity (DEC-022).

Content is approved and published by deterministic code, never by a person. Rows that need a
reviewer or publisher (``catalog_publications.published_by_account_id``,
``place_closure_rules.reviewed_by_account_id``, audit events) point at this seeded account.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account

SYSTEM_ACCOUNT_CLERK_USER_ID = "system:gonarra-pipeline"


async def system_account_id(session: AsyncSession) -> uuid.UUID:
    """Return the pipeline account id, creating the row if the seed has not run yet."""
    account_id = await session.scalar(
        select(Account.id).where(Account.clerk_user_id == SYSTEM_ACCOUNT_CLERK_USER_ID)
    )
    if account_id is not None:
        return account_id
    await session.execute(
        insert(Account)
        .values(clerk_user_id=SYSTEM_ACCOUNT_CLERK_USER_ID)
        .on_conflict_do_nothing(index_elements=[Account.clerk_user_id])
    )
    account_id = await session.scalar(
        select(Account.id).where(Account.clerk_user_id == SYSTEM_ACCOUNT_CLERK_USER_ID)
    )
    assert account_id is not None
    return account_id

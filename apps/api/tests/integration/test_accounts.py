import uuid

import pytest
from sqlalchemy import delete, func, select

from app.db.session import session_factory
from app.models.account import Account
from app.repositories.accounts import SQLAlchemyAccountRepository

pytestmark = pytest.mark.integration


async def test_account_mapping_is_idempotent() -> None:
    clerk_user_id = f"integration_{uuid.uuid4()}"
    async with session_factory() as session:
        repository = SQLAlchemyAccountRepository(session)
        first = await repository.get_or_create(clerk_user_id)
        second = await repository.get_or_create(clerk_user_id)
        count = await session.scalar(
            select(func.count()).select_from(Account).where(Account.clerk_user_id == clerk_user_id)
        )
        assert first.id == second.id
        assert count == 1
        await session.execute(delete(Account).where(Account.clerk_user_id == clerk_user_id))
        await session.commit()

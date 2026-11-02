from typing import Protocol

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository(Protocol):
    async def get_or_create(self, clerk_user_id: str) -> Account: ...


class SQLAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, clerk_user_id: str) -> Account:
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

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()
# hide_parameters: bound values (Guide questions, request text, coordinates) never appear in
# SQLAlchemy exception messages, so they cannot reach logs (privacy rule, BR-046).
engine = create_async_engine(settings.database_url, pool_pre_ping=True, hide_parameters=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session

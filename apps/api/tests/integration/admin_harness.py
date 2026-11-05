"""Shared integration fixtures for the curator API: one outer transaction per test.

Services commit their own unit of work; with ``join_transaction_mode="create_savepoint"`` each
commit only releases a savepoint, and the outer transaction is rolled back at teardown, so
tests never leave rows behind (other agents share the Compose database).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.routes.admin import get_chunk_embedder
from app.config import Settings, get_settings
from app.curation.embedding import Embedding
from app.db.session import get_db_session
from app.main import create_app
from app.security.clerk import AuthenticatedUser, get_current_user


@dataclass
class SwitchableEmbedder:
    """Fake chunk embedder: PENDING while disabled, deterministic unit vector when enabled."""

    enabled: bool = False
    calls: list[str] = field(default_factory=list)

    async def embed(self, text: str) -> Embedding | None:
        self.calls.append(text)
        if not self.enabled:
            return None
        vector: Sequence[float] = [1.0] + [0.0] * 767
        return Embedding(vector=list(vector), model="gemini-embedding-001")


@dataclass
class AdminHarness:
    client: AsyncClient
    session: AsyncSession
    embedder: SwitchableEmbedder
    curator_subject: str


@pytest.fixture
async def admin() -> AsyncIterator[AdminHarness]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    subject = f"it_curator_{uuid.uuid4().hex[:12]}"
    embedder = SwitchableEmbedder()
    settings = Settings(_env_file=None, curator_clerk_user_ids=subject)  # type: ignore[call-arg]

    async def session_override() -> AsyncIterator[AsyncSession]:
        yield session

    app: FastAPI = create_app()
    app.dependency_overrides[get_db_session] = session_override
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(subject, None)
    app.dependency_overrides[get_chunk_embedder] = lambda: embedder
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        try:
            yield AdminHarness(client, session, embedder, subject)
        finally:
            await session.close()
            await transaction.rollback()
            await connection.close()
            await engine.dispose()

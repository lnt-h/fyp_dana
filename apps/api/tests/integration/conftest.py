"""Integration-package fixtures: make the suite self-contained on a freshly migrated database.

CI (and anyone else) runs ``alembic upgrade head`` and then ``pytest -m integration``; the
reference seed (city ``da-nang``, areas, categories, fact fields, providers, policies) must exist
before any test. ``seed_reference_data`` is idempotent, so running it once per session against
the configured database is safe on an already-seeded dev DB too.
"""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.cli import seed_reference_data
from app.config import get_settings


async def _seed() -> None:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    try:
        async with AsyncSession(engine, expire_on_commit=False) as session:
            await seed_reference_data(session)  # commits its own unit of work
    finally:
        await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def reference_seed() -> None:
    """Upsert reference data once, before the first integration test runs."""
    asyncio.run(_seed())

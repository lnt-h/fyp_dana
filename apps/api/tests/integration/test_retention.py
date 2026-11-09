"""``caches sweep`` against PostgreSQL: expired rows go, Places lat/lng is cleared, idempotent."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.db.retention import sweep_caches

pytestmark = pytest.mark.integration


@pytest.fixture
async def maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


async def test_sweep_removes_expired_rows_and_old_coordinates(
    maker: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime.now(UTC)
    tag = uuid.uuid4().hex
    async with maker() as session:
        policy = await session.scalar(text("SELECT id FROM provider_policies LIMIT 1"))
        assert policy is not None
        old, fresh = now - timedelta(days=8), now - timedelta(hours=1)
        for key, fetched in ((f"old-{tag}", old), (f"new-{tag}", fresh)):
            await session.execute(
                text(
                    "INSERT INTO research_cache (provider, key_sha256, payload, provider_policy_id,"
                    " fetched_at, expires_at) VALUES ('TAVILY', :k, '{}'::jsonb, :p, :f, :e)"
                ),
                {"k": _sha(key), "p": policy, "f": fetched, "e": fetched + timedelta(days=7)},
            )
        # Location expired, outcome still valid: coordinates cleared, row kept.
        fetched = now - timedelta(hours=2)
        await session.execute(
            text(
                "INSERT INTO places_lookup_cache (query_sha256, google_place_id, outcome, location,"
                " location_expires_at, provider_policy_id, fetched_at, outcome_expires_at) VALUES"
                " (:q, :g, 'EXISTS_OPERATIONAL', ST_GeogFromText('POINT(108.2 16.05)'), :le, :p,"
                " :f, :oe)"
            ),
            {
                "q": _sha(f"loc-{tag}"),
                "g": f"g-{tag}",
                "le": fetched + timedelta(hours=1),
                "p": policy,
                "f": fetched,
                "oe": fetched + timedelta(hours=24),
            },
        )
        await session.commit()

    async with maker() as session:
        first = await sweep_caches(session, now=now)
    assert first.deleted["research_cache"] >= 1 and first.places_locations_cleared >= 1

    async with maker() as session:
        keys = set(
            (
                await session.scalars(
                    text("SELECT key_sha256 FROM research_cache WHERE key_sha256 IN (:a, :b)"),
                    {"a": _sha(f"old-{tag}"), "b": _sha(f"new-{tag}")},
                )
            ).all()
        )
        assert keys == {_sha(f"new-{tag}")}
        row = (
            await session.execute(
                text(
                    "SELECT location IS NULL AS gone, location_expires_at FROM places_lookup_cache"
                    " WHERE google_place_id = :g"
                ),
                {"g": f"g-{tag}"},
            )
        ).one()
        assert row.gone and row.location_expires_at is None

    async with maker() as session:
        again = await sweep_caches(session, now=now)
    assert again.deleted["research_cache"] == 0 and again.places_locations_cleared == 0

    async with maker() as session:
        await session.execute(
            text("DELETE FROM research_cache WHERE key_sha256 = :k"), {"k": _sha(f"new-{tag}")}
        )
        await session.execute(
            text("DELETE FROM places_lookup_cache WHERE google_place_id = :g"), {"g": f"g-{tag}"}
        )
        await session.commit()

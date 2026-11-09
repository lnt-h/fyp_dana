"""SqlMatrixCache against PostgreSQL (migration 0004 CHECKs, google_routes policy, expiry)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.cli import seed_reference_data
from app.config import get_settings
from app.routing.matrix_cache import CachedLeg, SqlMatrixCache

pytestmark = pytest.mark.integration


@pytest.fixture
async def factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        await seed_reference_data(session)
    try:
        yield maker
    finally:
        await engine.dispose()


async def _cleanup(factory: async_sessionmaker[AsyncSession], prefix: str) -> None:
    async with factory() as session:
        await session.execute(
            text("DELETE FROM routes_matrix_cache WHERE origin_key LIKE :p"), {"p": f"{prefix}%"}
        )
        await session.commit()


_ROUTES_POLICIES = (
    "FROM provider_policies pp JOIN data_providers dp ON dp.id = pp.data_provider_id "
    "WHERE dp.provider_key = 'google_routes'"
)


@pytest.fixture
async def active_routes_policy(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[uuid.UUID]:
    """The ACTIVE google_routes policy; a seeded DRAFT is activated for the test and reverted."""
    async with factory() as session:
        active = await session.scalar(text(f"SELECT pp.id {_ROUTES_POLICIES} AND status='ACTIVE'"))
        activated: uuid.UUID | None = None
        if active is None:
            activated = await session.scalar(
                text(
                    f"SELECT pp.id {_ROUTES_POLICIES} AND status='DRAFT' "
                    "ORDER BY policy_revision DESC LIMIT 1"
                )
            )
            assert activated is not None, "seed creates a google_routes policy"
            await session.execute(
                text(
                    "UPDATE provider_policies SET status='ACTIVE', approved_at=now() WHERE id = :id"
                ),
                {"id": activated},
            )
            await session.commit()
            active = activated
    try:
        yield active
    finally:
        if activated is not None:
            async with factory() as session:
                await session.execute(
                    text(
                        "UPDATE provider_policies SET status='DRAFT', approved_at=NULL "
                        "WHERE id = :id"
                    ),
                    {"id": activated},
                )
                await session.commit()


async def test_no_active_policy_caches_nothing(
    factory: async_sessionmaker[AsyncSession],
) -> None:
    """Only an ACTIVE google_routes policy may cover cached rows (never DRAFT or RETIRED)."""
    async with factory() as session:
        if await session.scalar(text(f"SELECT pp.id {_ROUTES_POLICIES} AND status='ACTIVE'")):
            pytest.skip("an ACTIVE google_routes policy exists in this database")
    tag = uuid.uuid4().hex[:8]
    cache = SqlMatrixCache(factory)
    try:
        written = await cache.write(
            [CachedLeg(f"anchor:it-{tag}-a", f"place:it-{tag}-b", True, 100, 60)],
            "DRIVE",
            now=datetime.now(UTC),
        )
        assert written == 0
    finally:
        await _cleanup(factory, "anchor:it-")


async def test_write_read_expiry_and_upsert(
    factory: async_sessionmaker[AsyncSession], active_routes_policy: uuid.UUID
) -> None:
    tag = uuid.uuid4().hex[:8]
    a, b, c = f"anchor:it-{tag}-a", f"place:it-{tag}-b", f"web:it-{tag}-c"
    cache = SqlMatrixCache(factory)
    now = datetime.now(UTC)
    try:
        written = await cache.write(
            [
                CachedLeg(a, b, True, 1200, 300),
                CachedLeg(b, a, False, None, None),
                CachedLeg(a, a, True, 0, 0),  # self pair is skipped (CHECK origin <> destination)
            ],
            "DRIVE",
            now=now,
        )
        assert written == 2

        legs = await cache.read([a, b, c], "DRIVE", now=now)
        assert legs[(a, b)] == CachedLeg(a, b, True, 1200, 300)
        assert legs[(b, a)] == CachedLeg(b, a, False, None, None)
        assert await cache.read([a, b], "WALK", now=now) == {}

        # Policy and TTL: fetched_at = now, expires_at = now + 30 d (CHECK upper bound).
        async with factory() as session:
            row = (
                await session.execute(
                    text(
                        "SELECT r.expires_at - r.fetched_at AS ttl, dp.provider_key, "
                        "pp.id AS policy_id "
                        "FROM routes_matrix_cache r "
                        "JOIN provider_policies pp ON pp.id = r.provider_policy_id "
                        "JOIN data_providers dp ON dp.id = pp.data_provider_id "
                        "WHERE r.origin_key = :a AND r.destination_key = :b"
                    ),
                    {"a": a, "b": b},
                )
            ).one()
        assert row.ttl == timedelta(days=30)
        assert row.provider_key == "google_routes"
        assert row.policy_id == active_routes_policy

        # Expired rows are invisible.
        assert await cache.read([a, b], "DRIVE", now=now + timedelta(days=30, seconds=1)) == {}

        # Upsert refreshes the measurement.
        later = now + timedelta(days=2)
        await cache.write([CachedLeg(a, b, True, 1300, 320)], "DRIVE", now=later)
        legs = await cache.read([a, b], "DRIVE", now=later)
        assert legs[(a, b)].duration_s == 320
    finally:
        await _cleanup(factory, "anchor:it-")
        await _cleanup(factory, "place:it-")
        await _cleanup(factory, "web:it-")


def test_ttl_cannot_exceed_policy() -> None:
    with pytest.raises(ValueError):
        SqlMatrixCache(lambda: None, ttl=timedelta(days=31))  # type: ignore[arg-type,return-value]

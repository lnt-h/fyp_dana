"""``routes_matrix_cache`` repository (ADR-006 google_routes EPHEMERAL ≤ 30 d, ADR-011).

Rows are keyed ``(origin_key, destination_key, travel_mode)`` with keys ``place:<uuid>``,
``web:<uuid>`` or ``anchor:<code>`` — never traveler GPS. Only Google measurements are written
(AVAILABLE, or UNAVAILABLE when Google reports no route); transient failures, quota denials and
estimates are never cached. Rows are written only under the ACTIVE ``google_routes`` provider
policy (never DRAFT or RETIRED). Each operation is a short transaction of its own.
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Callable, Iterable, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.caches import RoutesMatrixCache
from app.routing.provider import TravelMode

logger = logging.getLogger("gonarra.routing")

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]

# ADR-006: google_routes distance_m / duration_s are EPHEMERAL ≤ 30 d (CHECK in migration 0004).
ROUTES_CACHE_TTL = timedelta(days=30)
ROUTES_PROVIDER_KEY = "google_routes"
CACHE_KEY_RE = re.compile(r"^(place|web|anchor):[a-z0-9-]{1,64}$")


def validate_cache_key(key: str) -> str:
    if not CACHE_KEY_RE.match(key):
        raise ValueError(f"invalid routes cache key: {key!r}")
    return key


@dataclass(frozen=True, slots=True)
class CachedLeg:
    origin_key: str
    destination_key: str
    available: bool
    distance_m: int | None
    duration_s: int | None


class MatrixCache(Protocol):
    async def read(
        self, keys: Sequence[str], mode: TravelMode, *, now: datetime
    ) -> dict[tuple[str, str], CachedLeg]:
        """Unexpired legs among ``keys`` × ``keys`` for ``mode``."""
        ...

    async def write(self, legs: Iterable[CachedLeg], mode: TravelMode, *, now: datetime) -> int:
        """Upsert legs with ``fetched_at = now`` and ``expires_at = now + 30 d``."""
        ...


# Only the ACTIVE google_routes policy (owner-approved terms, ADR-006) may cover cached rows; a
# DRAFT or RETIRED policy never does, so without an ACTIVE one nothing is cached.
_POLICY_ID = text(
    "SELECT pp.id FROM provider_policies pp "
    "JOIN data_providers dp ON dp.id = pp.data_provider_id "
    "WHERE dp.provider_key = :provider_key AND pp.status = 'ACTIVE' "
    "ORDER BY pp.policy_revision DESC LIMIT 1"
)


class SqlMatrixCache:
    def __init__(self, session_factory: SessionFactory, *, ttl: timedelta = ROUTES_CACHE_TTL):
        if ttl > ROUTES_CACHE_TTL or ttl <= timedelta(0):
            raise ValueError("routes cache TTL must be within (0, 30 d] (ADR-006)")
        self._session_factory = session_factory
        self._ttl = ttl
        self._policy_id: uuid.UUID | None = None

    async def _routes_policy_id(self, session: AsyncSession) -> uuid.UUID | None:
        if self._policy_id is None:
            value = await session.scalar(_POLICY_ID, {"provider_key": ROUTES_PROVIDER_KEY})
            self._policy_id = value if isinstance(value, uuid.UUID) else None
        return self._policy_id

    async def read(
        self, keys: Sequence[str], mode: TravelMode, *, now: datetime
    ) -> dict[tuple[str, str], CachedLeg]:
        if len(keys) < 2:
            return {}
        key_list = sorted(set(keys))
        stmt = select(RoutesMatrixCache).where(
            RoutesMatrixCache.travel_mode == mode,
            RoutesMatrixCache.origin_key.in_(key_list),
            RoutesMatrixCache.destination_key.in_(key_list),
            RoutesMatrixCache.expires_at > now,
        )
        async with self._session_factory() as session:
            rows = (await session.scalars(stmt)).all()
        return {
            (row.origin_key, row.destination_key): CachedLeg(
                origin_key=row.origin_key,
                destination_key=row.destination_key,
                available=row.availability == "AVAILABLE",
                distance_m=row.distance_m,
                duration_s=row.duration_s,
            )
            for row in rows
        }

    async def write(self, legs: Iterable[CachedLeg], mode: TravelMode, *, now: datetime) -> int:
        expires_at = now + self._ttl
        values: list[dict[str, object]] = [
            {
                "origin_key": leg.origin_key,
                "destination_key": leg.destination_key,
                "travel_mode": mode,
                "availability": "AVAILABLE" if leg.available else "UNAVAILABLE",
                "distance_m": leg.distance_m if leg.available else None,
                "duration_s": leg.duration_s if leg.available else None,
                "fetched_at": now,
                "expires_at": expires_at,
            }
            for leg in legs
            if leg.origin_key != leg.destination_key
        ]
        if not values:
            return 0
        async with self._session_factory() as session:
            policy_id = await self._routes_policy_id(session)
            if policy_id is None:
                logger.warning("routes cache_write_skipped reason=no_active_google_routes_policy")
                return 0
            for row in values:
                row["provider_policy_id"] = policy_id
            stmt = insert(RoutesMatrixCache).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    RoutesMatrixCache.origin_key,
                    RoutesMatrixCache.destination_key,
                    RoutesMatrixCache.travel_mode,
                ],
                set_={
                    "availability": stmt.excluded.availability,
                    "distance_m": stmt.excluded.distance_m,
                    "duration_s": stmt.excluded.duration_s,
                    "provider_policy_id": stmt.excluded.provider_policy_id,
                    "fetched_at": stmt.excluded.fetched_at,
                    "expires_at": stmt.excluded.expires_at,
                },
            )
            await session.execute(stmt)
            await session.commit()
        return len(values)

"""Measure the legs a manual edit changed (ADR-011: "the retimer measures only changed legs").

The editor (:mod:`app.trips.snapshot`) asks for ``(from place, to place, mode)`` legs; this module
resolves the places' coordinates server-side, reads the routes cache and fetches misses through the
configured routing provider under the quota ledger (:func:`app.routing.matrix.get_matrix`). It
never raises: a leg it cannot measure is simply absent and stays ``EXPIRED``. Coordinates are never
logged (AGENTS.md).
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Sequence
from contextlib import AbstractAsyncContextManager
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.quota import QuotaLedger
from app.config import Settings
from app.models.providers import DataProvider
from app.observability import log_failure
from app.routing.matrix import get_matrix
from app.routing.matrix_cache import ROUTES_PROVIDER_KEY
from app.routing.provider import (
    EstimateNotAllowedError,
    LatLng,
    NoRoutesProvider,
    RoutesProvider,
    select_provider,
)
from app.trips.repository import ROUTES_ESTIMATE_PROVIDER_KEY
from app.trips.snapshot import LegKey, LegMeasurement

logger = logging.getLogger("gonarra.trips")

SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]
GOOGLE_TTL = timedelta(days=30)

_COORDS = text(
    "SELECT id, ST_Y(location::geometry) AS lat, ST_X(location::geometry) AS lng "
    "FROM places WHERE id = ANY(:ids)"
)


class LegMeasurer(Protocol):
    async def measure(self, legs: Sequence[LegKey]) -> dict[LegKey, LegMeasurement]: ...


def _key(place_id: uuid.UUID) -> str:
    return f"place:{place_id}"


class RoutingLegMeasurer:
    """:class:`LegMeasurer` over the routes cache and the configured routing provider."""

    def __init__(
        self,
        session_factory: SessionFactory,
        settings: Settings,
        *,
        provider: RoutesProvider | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._sf = session_factory
        self._settings = settings
        self._provider = provider
        self._clock = clock or (lambda: datetime.now(UTC))

    def _routes_provider(self) -> RoutesProvider:
        if self._provider is not None:
            return self._provider
        try:
            return select_provider(
                self._settings, estimate_enabled=self._settings.routes_estimate_enabled
            )
        except EstimateNotAllowedError:
            return NoRoutesProvider()

    async def measure(self, legs: Sequence[LegKey]) -> dict[LegKey, LegMeasurement]:
        if not legs:
            return {}
        try:
            return await self._measure(legs)
        except Exception as exc:  # noqa: BLE001 - an unmeasured leg stays EXPIRED
            log_failure(logger, "edit_leg_measure_failed", exc)
            return {}

    async def _measure(self, legs: Sequence[LegKey]) -> dict[LegKey, LegMeasurement]:
        ids = sorted({place for a, b, _ in legs for place in (a, b)}, key=str)
        async with self._sf() as session:
            rows = (await session.execute(_COORDS, {"ids": ids})).all()
            providers = {
                key: await _ensure_provider(session, key, name)
                for key, name in (
                    (ROUTES_PROVIDER_KEY, "Google Routes API"),
                    (ROUTES_ESTIMATE_PROVIDER_KEY, "Gonarra straight-line estimate (demo only)"),
                )
            }
            await session.commit()
        coords = {row.id: LatLng(float(row.lat), float(row.lng)) for row in rows}
        provider = self._routes_provider()
        ledger = QuotaLedger(self._sf, self._settings, clock=self._clock)
        now = self._clock()
        out: dict[LegKey, LegMeasurement] = {}
        for mode in sorted({mode for _, _, mode in legs}):
            wanted = [(a, b) for a, b, m in legs if m == mode and a in coords and b in coords]
            if not wanted:
                continue
            keys = {_key(p): coords[p] for pair in wanted for p in pair}
            matrix = await get_matrix(
                self._sf, keys_with_coords=keys, mode=mode, ledger=ledger, provider=provider
            )
            for a, b in wanted:
                leg = matrix.leg(_key(a), _key(b))
                if not leg.available or leg.distance_m is None or leg.duration_s is None:
                    continue
                out[(a, b, mode)] = LegMeasurement(
                    distance_m=leg.distance_m,
                    duration_s=leg.duration_s,
                    data_provider_id=providers[
                        ROUTES_ESTIMATE_PROVIDER_KEY if leg.estimated else ROUTES_PROVIDER_KEY
                    ],
                    measured_at=now,
                    expires_at=None if leg.estimated else now + GOOGLE_TTL,
                    estimated=leg.estimated,
                )
        return out


async def _ensure_provider(session: AsyncSession, key: str, display_name: str) -> uuid.UUID:
    await session.execute(
        insert(DataProvider)
        .values(provider_key=key, display_name=display_name, provider_kind="RUNTIME_API")
        .on_conflict_do_nothing(index_elements=[DataProvider.provider_key])
    )
    provider_id = await session.scalar(
        select(DataProvider.id).where(DataProvider.provider_key == key)
    )
    if provider_id is None:  # pragma: no cover - the upsert above guarantees a row
        raise RuntimeError("data provider missing")
    return provider_id

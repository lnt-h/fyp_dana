"""In-memory quota ledger and matrix cache for routing unit tests (no DB, no live Google)."""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

import httpx

from app.ai.quota import Bucket, QuotaDecision, QuotaReservation
from app.routing.matrix_cache import ROUTES_CACHE_TTL, CachedLeg
from app.routing.provider import TravelMode

NOW = datetime(2026, 11, 6, 3, 0, tzinfo=UTC)


@dataclass
class FakeLedger:
    cap: int = 10_000
    used: int = 0
    reserved: int = 0
    reserve_calls: list[int] = field(default_factory=list)

    async def reserve(self, *, bucket: Bucket, amount: int = 1) -> QuotaDecision:
        assert bucket is Bucket.ROUTES_ELEMENTS
        self.reserve_calls.append(amount)
        if self.used + self.reserved + amount > self.cap:
            return QuotaDecision(False, bucket, self.cap - self.used - self.reserved)
        self.reserved += amount
        reservation = QuotaReservation(uuid.uuid4(), bucket, amount, None, date(2026, 11, 6))
        return QuotaDecision(True, bucket, self.cap - self.used - self.reserved, reservation)

    async def commit(self, reservation: QuotaReservation) -> None:
        self.reserved -= reservation.amount
        self.used += reservation.amount

    async def release(self, reservation: QuotaReservation) -> None:
        self.reserved -= reservation.amount


@dataclass
class FakeCache:
    rows: dict[tuple[str, str, str], tuple[CachedLeg, datetime]] = field(default_factory=dict)
    writes: list[CachedLeg] = field(default_factory=list)

    def put(self, leg: CachedLeg, mode: TravelMode, expires_at: datetime) -> None:
        self.rows[(leg.origin_key, leg.destination_key, mode)] = (leg, expires_at)

    async def read(
        self, keys: Sequence[str], mode: TravelMode, *, now: datetime
    ) -> dict[tuple[str, str], CachedLeg]:
        wanted = set(keys)
        return {
            (o, d): leg
            for (o, d, m), (leg, expires) in self.rows.items()
            if m == mode and o in wanted and d in wanted and expires > now
        }

    async def write(self, legs: Iterable[CachedLeg], mode: TravelMode, *, now: datetime) -> int:
        count = 0
        for leg in legs:
            self.put(leg, mode, now + ROUTES_CACHE_TTL)
            self.writes.append(leg)
            count += 1
        return count


def matrix_callback(
    *, no_route: set[tuple[int, int]] | None = None, seconds_per_index: int = 60
) -> Any:
    """pytest-httpx callback answering computeRouteMatrix like Google (proto3 zero omission)."""

    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        out: list[dict[str, Any]] = []
        for oi, _ in enumerate(body["origins"]):
            for di, _ in enumerate(body["destinations"]):
                element: dict[str, Any] = {}
                if oi:
                    element["originIndex"] = oi
                if di:
                    element["destinationIndex"] = di
                if no_route and (oi, di) in no_route:
                    element["condition"] = "ROUTE_NOT_FOUND"
                else:
                    element["condition"] = "ROUTE_EXISTS"
                    element["distanceMeters"] = 1000 + 10 * oi + di
                    element["duration"] = f"{seconds_per_index * (1 + oi + di)}s"
                out.append(element)
        return httpx.Response(200, json=out)

    return respond

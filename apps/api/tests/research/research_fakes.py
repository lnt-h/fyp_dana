"""In-memory ResearchStore and quota ledger for research adapter tests."""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import UTC, date, datetime
from typing import Any

from app.ai.quota import Bucket, QuotaDecision, QuotaReservation
from app.research.store import CachedEntry, PlacesLookup

POLICY = uuid.UUID("22222222-2222-4222-8222-222222222222")


class MemoryStore:
    def __init__(self, *, inside_city: bool | None = True) -> None:
        self.cache: dict[tuple[str, str], CachedEntry] = {}
        self.revisions: list[dict[str, Any]] = []
        self.places: dict[str, dict[str, Any]] = {}
        self.inside_city = inside_city

    async def policy_id(self, provider_key: str) -> uuid.UUID | None:
        return POLICY

    async def get_cached(self, provider: str, key_sha256: str) -> CachedEntry | None:
        return self.cache.get((provider, key_sha256))

    async def put_cached(
        self,
        provider: str,
        key_sha256: str,
        payload: dict[str, Any],
        *,
        policy_id: uuid.UUID,
        source_revision_id: uuid.UUID | None = None,
    ) -> None:
        self.cache[(provider, key_sha256)] = CachedEntry(
            payload, source_revision_id, datetime.now(UTC)
        )

    async def append_source_revision(
        self, *, url: str, title: str | None, content_sha256: str, retrieved_at: datetime
    ) -> uuid.UUID | None:
        rid = uuid.uuid4()
        self.revisions.append({"id": rid, "url": url, "sha": content_sha256, "title": title})
        return rid

    async def get_places_lookup(self, query_sha256: str) -> PlacesLookup | None:
        row = self.places.get(query_sha256)
        return None if row is None else PlacesLookup(row["outcome"], row["gid"], row["at"])

    async def put_places_lookup(self, **kw: Any) -> None:
        self.places[kw["query_sha256"]] = {
            "outcome": kw["outcome"],
            "gid": kw["google_place_id"],
            "at": datetime.now(UTC),
            "lat": kw["lat"],
        }

    async def point_in_city(self, city_code: str, lat: float, lng: float) -> bool | None:
        return self.inside_city


class FakeLedger:
    def __init__(self, caps: dict[Bucket, int] | None = None) -> None:
        self.caps = caps or {}
        self.used: Counter[Bucket] = Counter()
        self.reserved: Counter[Bucket] = Counter()

    async def reserve(
        self, *, bucket: Bucket, amount: int = 1, account_id: uuid.UUID | None = None
    ) -> QuotaDecision:
        cap = self.caps.get(bucket, 100)
        if self.used[bucket] + self.reserved[bucket] + amount > cap:
            return QuotaDecision(False, bucket, 0)
        self.reserved[bucket] += amount
        res = QuotaReservation(uuid.uuid4(), bucket, amount, None, date(2026, 11, 6))
        return QuotaDecision(True, bucket, cap, res)

    async def commit(self, reservation: QuotaReservation) -> None:
        self.reserved[reservation.bucket] -= reservation.amount
        self.used[reservation.bucket] += reservation.amount

    async def release(self, reservation: QuotaReservation) -> None:
        self.reserved[reservation.bucket] -= reservation.amount


async def public_resolver(host: str) -> list[str]:
    return ["93.184.216.34"]


async def private_resolver(host: str) -> list[str]:
    return ["10.0.0.5"]

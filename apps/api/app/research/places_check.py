"""Google Places existence/status check for web candidates (FR-100, ADR-006, ADR-014).

Returns Gonarra's own verdict (``EXISTS_OPERATIONAL``, ``EXISTS_CLOSED``, ``NOT_FOUND``,
``OUTSIDE_CITY``) or ``SKIPPED`` when no Google key is configured, the ``PLACES`` budget is
spent or the call fails. Minimal field mask (id, businessStatus, location). Only ``place_id``
is kept canonically; the location is an ephemeral copy in ``places_lookup_cache`` (≤ 30 d)
used for the city check; ``businessStatus`` is used at runtime only (DENY).
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import httpx

from app.agents.validators import normalise_text
from app.ai.quota import Bucket, QuotaLedger
from app.ai.redaction import RedactionError, ensure_clean, redact_text
from app.research.store import ResearchStore

logger = logging.getLogger("gonarra.research")

SEARCH_TEXT_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = "places.id,places.businessStatus,places.location"
TIMEOUT_S = 10.0
# Rectangle bias around the post-merger city envelope (cli DA_NANG_BOUNDARY_EWKT).
_BIAS = {
    "rectangle": {
        "low": {"latitude": 14.90, "longitude": 107.20},
        "high": {"latitude": 16.35, "longitude": 108.95},
    }
}


class PlacesOutcome(StrEnum):
    EXISTS_OPERATIONAL = "EXISTS_OPERATIONAL"
    EXISTS_CLOSED = "EXISTS_CLOSED"
    NOT_FOUND = "NOT_FOUND"
    OUTSIDE_CITY = "OUTSIDE_CITY"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True, slots=True)
class PlacesCheckResult:
    outcome: PlacesOutcome
    google_place_id: str | None = None
    checked_at: datetime | None = None  # None exactly when SKIPPED (ck_..._places_checked)
    cached: bool = False


def lookup_query(name: str, city_name: str) -> str:
    return ensure_clean(" ".join(f"{redact_text(name)}, {city_name}".split())[:200])


def lookup_key(query: str) -> str:
    return hashlib.sha256(normalise_text(query).encode("utf-8")).hexdigest()


class PlacesChecker:
    def __init__(
        self,
        *,
        api_key: str | None,
        ledger: QuotaLedger,
        store: ResearchStore,
        city_code: str = "da-nang",
        city_name: str = "Đà Nẵng",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._key = api_key or None
        self._ledger = ledger
        self._store = store
        self._city_code = city_code
        self._city_name = city_name
        self._client = client

    @property
    def enabled(self) -> bool:
        return self._key is not None

    async def check(self, name: str) -> PlacesCheckResult:
        if self._key is None:
            return PlacesCheckResult(PlacesOutcome.SKIPPED)
        try:
            query = lookup_query(name, self._city_name)
        except RedactionError:
            return PlacesCheckResult(PlacesOutcome.SKIPPED)
        key = lookup_key(query)
        cached = await self._store.get_places_lookup(key)
        if cached is not None:
            return PlacesCheckResult(
                PlacesOutcome(cached.outcome), cached.google_place_id, cached.fetched_at, True
            )
        decision = await self._ledger.reserve(bucket=Bucket.PLACES)
        if decision.reservation is None:
            return PlacesCheckResult(PlacesOutcome.SKIPPED)
        try:
            data = await self._search(query)
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("places error=%s", type(exc).__name__)
            data = None
        finally:
            await self._ledger.commit(decision.reservation)
        if data is None:
            return PlacesCheckResult(PlacesOutcome.SKIPPED)

        places = data.get("places") or []
        now = datetime.now(UTC)
        lat = lng = None
        if not places:
            outcome, place_id = PlacesOutcome.NOT_FOUND, None
        else:
            top = places[0]
            place_id = str(top.get("id") or "") or None
            location = top.get("location") or {}
            lat, lng = location.get("latitude"), location.get("longitude")
            inside = (
                await self._store.point_in_city(self._city_code, float(lat), float(lng))
                if lat is not None and lng is not None
                else None
            )
            if place_id is None:
                outcome = PlacesOutcome.NOT_FOUND
            elif inside is False:
                outcome = PlacesOutcome.OUTSIDE_CITY
            elif top.get("businessStatus") in {"CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"}:
                outcome = PlacesOutcome.EXISTS_CLOSED
            else:
                outcome = PlacesOutcome.EXISTS_OPERATIONAL
        policy = await self._store.policy_id("google_places")
        if policy is not None:
            await self._store.put_places_lookup(
                query_sha256=key,
                outcome=outcome.value,
                google_place_id=place_id,
                lat=lat,
                lng=lng,
                policy_id=policy,
            )
        return PlacesCheckResult(outcome, place_id, now)

    async def _search(self, query: str) -> dict[str, Any]:
        assert self._key is not None
        client = self._client or httpx.AsyncClient(timeout=TIMEOUT_S)
        try:
            response = await client.post(
                SEARCH_TEXT_URL,
                json={"textQuery": query, "maxResultCount": 1, "locationBias": _BIAS},
                headers={"X-Goog-Api-Key": self._key, "X-Goog-FieldMask": FIELD_MASK},
            )
            response.raise_for_status()
            payload = response.json()
        finally:
            if self._client is None:
                await client.aclose()
        if not isinstance(payload, dict):
            raise ValueError("unexpected Places payload")
        return payload

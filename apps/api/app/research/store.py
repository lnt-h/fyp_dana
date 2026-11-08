"""Persistence for research adapters: ``research_cache``, ``sources``/``source_revisions``,
``places_lookup_cache`` and provider-policy lookup (ADR-006, migration 0004).

Each method is a short transaction of its own (never held across a provider call). The
:class:`ResearchStore` protocol lets unit tests use an in-memory fake.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from urllib.parse import urlsplit

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError

from app.ai.quota import SessionFactory

logger = logging.getLogger("gonarra.research")

RESEARCH_CACHE_TTL = timedelta(days=7)  # tavily / web_page EPHEMERAL ≤ 7 d (OQ-122)
PLACES_OUTCOME_TTL = timedelta(hours=24)
PLACES_LOCATION_TTL = timedelta(days=30)  # google_places.location EPHEMERAL ≤ 30 d

TAVILY = "TAVILY"
WEB_PAGE = "WEB_PAGE"


@dataclass(frozen=True, slots=True)
class CachedEntry:
    payload: dict[str, Any]
    source_revision_id: uuid.UUID | None
    fetched_at: datetime


@dataclass(frozen=True, slots=True)
class PlacesLookup:
    outcome: str
    google_place_id: str | None
    fetched_at: datetime


class ResearchStore(Protocol):
    async def policy_id(self, provider_key: str) -> uuid.UUID | None: ...

    async def get_cached(self, provider: str, key_sha256: str) -> CachedEntry | None: ...

    async def put_cached(
        self,
        provider: str,
        key_sha256: str,
        payload: dict[str, Any],
        *,
        policy_id: uuid.UUID,
        source_revision_id: uuid.UUID | None = None,
    ) -> None: ...

    async def append_source_revision(
        self, *, url: str, title: str | None, content_sha256: str, retrieved_at: datetime
    ) -> uuid.UUID | None: ...

    async def get_places_lookup(self, query_sha256: str) -> PlacesLookup | None: ...

    async def put_places_lookup(
        self,
        *,
        query_sha256: str,
        outcome: str,
        google_place_id: str | None,
        lat: float | None,
        lng: float | None,
        policy_id: uuid.UUID,
    ) -> None: ...

    async def point_in_city(self, city_code: str, lat: float, lng: float) -> bool | None: ...


_POLICY = text(
    "/* research:policy */ SELECT pp.id, pp.status FROM provider_policies pp "
    "JOIN data_providers dp ON dp.id = pp.data_provider_id "
    "WHERE dp.provider_key = :key AND pp.status IN ('ACTIVE', 'DRAFT') "
    "ORDER BY (pp.status = 'ACTIVE') DESC, pp.policy_revision DESC LIMIT 1"
)
_CACHE_GET = text(
    "/* research:cache_get */ SELECT payload, source_revision_id, fetched_at FROM research_cache "
    "WHERE provider = :provider AND key_sha256 = :key AND expires_at > now()"
)
_CACHE_PUT = text(
    "/* research:cache_put */ INSERT INTO research_cache "
    "(provider, key_sha256, payload, source_revision_id, provider_policy_id, fetched_at, "
    "expires_at) VALUES (:provider, :key, :payload, :rev, :policy, :now, :expires) "
    "ON CONFLICT (provider, key_sha256) DO UPDATE SET payload = EXCLUDED.payload, "
    "source_revision_id = EXCLUDED.source_revision_id, "
    "provider_policy_id = EXCLUDED.provider_policy_id, fetched_at = EXCLUDED.fetched_at, "
    "expires_at = EXCLUDED.expires_at"
).bindparams(bindparam("payload", type_=JSONB))
_SOURCE_GET = text(
    "/* research:source_get */ SELECT id FROM sources "
    "WHERE source_kind = 'WEB' AND homepage_url = :home ORDER BY created_at LIMIT 1"
)
_SOURCE_PUT = text(
    "/* research:source_put */ INSERT INTO sources "
    "(data_provider_id, publisher, source_kind, homepage_url, license_code, attribution_text) "
    "VALUES ((SELECT id FROM data_providers WHERE provider_key = 'web_page'), :host, 'WEB', "
    ":home, 'UNKNOWN', :host) RETURNING id"
)
_REVISION_PUT = text(
    "/* research:revision_put */ INSERT INTO source_revisions "
    "(source_id, locator, title, retrieved_at, content_sha256) "
    "VALUES (:source_id, :url, :title, :retrieved_at, :sha) "
    "ON CONFLICT (source_id, locator, retrieved_at) DO NOTHING RETURNING id"
)
_PLACES_GET = text(
    "/* research:places_get */ SELECT outcome, google_place_id, fetched_at "
    "FROM places_lookup_cache WHERE query_sha256 = :key AND outcome_expires_at > now()"
)
_PLACES_PUT = text(
    "/* research:places_put */ INSERT INTO places_lookup_cache "
    "(query_sha256, google_place_id, outcome, location, location_expires_at, "
    "provider_policy_id, fetched_at, outcome_expires_at) VALUES (:key, :gid, :outcome, "
    "CASE WHEN CAST(:lng AS double precision) IS NULL THEN NULL "
    "ELSE ST_SetSRID(ST_MakePoint(CAST(:lng AS double precision), "
    "CAST(:lat AS double precision)), 4326)::geography END, "
    ":loc_expires, :policy, :now, :expires) "
    "ON CONFLICT (query_sha256) DO UPDATE SET google_place_id = EXCLUDED.google_place_id, "
    "outcome = EXCLUDED.outcome, location = EXCLUDED.location, "
    "location_expires_at = EXCLUDED.location_expires_at, fetched_at = EXCLUDED.fetched_at, "
    "outcome_expires_at = EXCLUDED.outcome_expires_at"
)
_IN_CITY = text(
    "/* research:in_city */ SELECT ST_Covers(boundary, "
    "ST_SetSRID(ST_MakePoint(CAST(:lng AS double precision), CAST(:lat AS double precision)), "
    "4326)::geography) AS inside "
    "FROM cities WHERE code = :code AND boundary IS NOT NULL"
)


def _home(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    return host, f"{parts.scheme.lower()}://{host}"


class SqlResearchStore:
    """PostgreSQL implementation. Database errors are logged and degrade (cache miss / no row);
    research never fails a request because of bookkeeping."""

    def __init__(self, session_factory: SessionFactory, *, allow_draft_policies: bool) -> None:
        self._sf = session_factory
        self._allow_draft = allow_draft_policies
        self._policies: dict[str, uuid.UUID | None] = {}

    async def policy_id(self, provider_key: str) -> uuid.UUID | None:
        if provider_key in self._policies:
            return self._policies[provider_key]
        row = await self._one(_POLICY, {"key": provider_key})
        policy: uuid.UUID | None = None
        if row is not None and (row["status"] == "ACTIVE" or self._allow_draft):
            policy = row["id"]
        if policy is None:
            logger.warning("research policy=%s missing_or_inactive persistence=off", provider_key)
        self._policies[provider_key] = policy
        return policy

    async def get_cached(self, provider: str, key_sha256: str) -> CachedEntry | None:
        row = await self._one(_CACHE_GET, {"provider": provider, "key": key_sha256})
        if row is None:
            return None
        return CachedEntry(dict(row["payload"]), row["source_revision_id"], row["fetched_at"])

    async def put_cached(
        self,
        provider: str,
        key_sha256: str,
        payload: dict[str, Any],
        *,
        policy_id: uuid.UUID,
        source_revision_id: uuid.UUID | None = None,
    ) -> None:
        now = datetime.now(UTC)
        await self._exec(
            _CACHE_PUT,
            {
                "provider": provider,
                "key": key_sha256,
                "payload": payload,
                "rev": source_revision_id,
                "policy": policy_id,
                "now": now,
                "expires": now + RESEARCH_CACHE_TTL - timedelta(seconds=1),
            },
        )

    async def append_source_revision(
        self, *, url: str, title: str | None, content_sha256: str, retrieved_at: datetime
    ) -> uuid.UUID | None:
        host, home = _home(url)
        try:
            async with self._sf() as session:
                source_id = (await session.execute(_SOURCE_GET, {"home": home})).scalar()
                if source_id is None:
                    source_id = (
                        await session.execute(_SOURCE_PUT, {"host": host, "home": home})
                    ).scalar_one()
                revision_id = (
                    await session.execute(
                        _REVISION_PUT,
                        {
                            "source_id": source_id,
                            "url": url,
                            "title": title[:500] if title else None,
                            "retrieved_at": retrieved_at,
                            "sha": content_sha256,
                        },
                    )
                ).scalar()
                await session.commit()
        except SQLAlchemyError:
            logger.warning("research source_revision not_recorded host=%s", host)
            return None
        return revision_id if isinstance(revision_id, uuid.UUID) else None

    async def get_places_lookup(self, query_sha256: str) -> PlacesLookup | None:
        row = await self._one(_PLACES_GET, {"key": query_sha256})
        if row is None:
            return None
        return PlacesLookup(row["outcome"], row["google_place_id"], row["fetched_at"])

    async def put_places_lookup(
        self,
        *,
        query_sha256: str,
        outcome: str,
        google_place_id: str | None,
        lat: float | None,
        lng: float | None,
        policy_id: uuid.UUID,
    ) -> None:
        now = datetime.now(UTC)
        has_location = lat is not None and lng is not None
        await self._exec(
            _PLACES_PUT,
            {
                "key": query_sha256,
                "gid": google_place_id,
                "outcome": outcome,
                "lat": lat if has_location else None,
                "lng": lng if has_location else None,
                "loc_expires": now + PLACES_LOCATION_TTL if has_location else None,
                "policy": policy_id,
                "now": now,
                "expires": now + PLACES_OUTCOME_TTL,
            },
        )

    async def point_in_city(self, city_code: str, lat: float, lng: float) -> bool | None:
        row = await self._one(_IN_CITY, {"code": city_code, "lat": lat, "lng": lng})
        return None if row is None else bool(row["inside"])

    async def _one(self, stmt: Any, params: dict[str, Any]) -> Any:
        try:
            async with self._sf() as session:
                return (await session.execute(stmt, params)).mappings().first()
        except SQLAlchemyError:
            logger.warning("research query failed op=%s", str(stmt).split("*/")[0][3:].strip())
            return None

    async def _exec(self, stmt: Any, params: dict[str, Any]) -> None:
        try:
            async with self._sf() as session:
                await session.execute(stmt, params)
                await session.commit()
        except SQLAlchemyError:
            logger.warning("research write failed op=%s", str(stmt).split("*/")[0][3:].strip())

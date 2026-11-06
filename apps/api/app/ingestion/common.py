"""Shared ingestion plumbing (ADR-006, ADR-012, DEC-022).

* Default deny: an importer runs only under the provider's ACTIVE policy and persists only the
  payload fields that policy allows (``ALLOW_CANONICAL`` / ``ALLOW_IDENTIFIER_ONLY``).
* Idempotency: a run whose (provider, city, release, checksum, importer version) already
  SUCCEEDED is skipped; places are keyed by ``external_place_identities``; source revisions are
  reused while the captured content hash is unchanged.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import normalize_search_text, slugify
from app.db.types import ewkt_point
from app.models.catalog import Place, Source, SourceRevision
from app.models.providers import (
    DataProvider,
    ExternalPlaceIdentity,
    ImportRecord,
    ImportRun,
    ProviderFieldRule,
    ProviderPolicy,
)
from app.models.reference import City

PERSISTABLE = frozenset({"ALLOW_CANONICAL", "ALLOW_IDENTIFIER_ONLY"})
# Gonarra's own provenance metadata inside import_records.allowed_payload (source revision ids):
# not a provider field, so the policy filter does not apply to it.
PROVENANCE_KEY = "_provenance"
USER_AGENT = "GonarraBot/0.1 (university FYP; https://github.com/lnt-h/fyp_dana)"


class PolicyNotActiveError(RuntimeError):
    """The provider has no ACTIVE policy: nothing may be imported from it (ADR-006)."""

    def __init__(self, provider_key: str) -> None:
        super().__init__(
            f"provider {provider_key!r} has no ACTIVE policy; run "
            f"`python -m app.cli policy activate {provider_key} --terms-version <text>` first"
        )
        self.provider_key = provider_key


@dataclass(frozen=True)
class ActivePolicy:
    provider_id: uuid.UUID
    provider_key: str
    policy_id: uuid.UUID
    attribution_text: str | None
    field_rules: Mapping[str, str]

    def allows(self, field_name: str) -> bool:
        return self.field_rules.get(field_name) in PERSISTABLE

    def filter_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Keep only fields with a persistable rule; a field without a rule is DENY."""
        return {key: value for key, value in payload.items() if self.allows(key)}


async def require_active_policy(session: AsyncSession, provider_key: str) -> ActivePolicy:
    row = (
        await session.execute(
            select(DataProvider.id, ProviderPolicy.id, ProviderPolicy.attribution_text)
            .join(ProviderPolicy, ProviderPolicy.data_provider_id == DataProvider.id)
            .where(DataProvider.provider_key == provider_key, ProviderPolicy.status == "ACTIVE")
        )
    ).first()
    if row is None:
        raise PolicyNotActiveError(provider_key)
    provider_id, policy_id, attribution = row
    rules = (
        await session.execute(
            select(ProviderFieldRule.field_name, ProviderFieldRule.persistence_class).where(
                ProviderFieldRule.provider_policy_id == policy_id
            )
        )
    ).all()
    return ActivePolicy(
        provider_id=provider_id,
        provider_key=provider_key,
        policy_id=policy_id,
        attribution_text=attribution,
        field_rules={name: persistence for name, persistence in rules},
    )


async def provider_id_for(session: AsyncSession, provider_key: str) -> uuid.UUID | None:
    return await session.scalar(
        select(DataProvider.id).where(DataProvider.provider_key == provider_key)
    )


# ---- Hashing ------------------------------------------------------------------------------


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_hex(value: str | bytes) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest()


# ---- City ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class CityContext:
    id: uuid.UUID
    code: str
    bbox: tuple[float, float, float, float] | None  # (min_lng, min_lat, max_lng, max_lat)


async def load_city(session: AsyncSession, city_code: str) -> CityContext:
    row = (
        await session.execute(
            text(
                "SELECT id, ST_XMin(b), ST_YMin(b), ST_XMax(b), ST_YMax(b) "
                "FROM (SELECT id, Box2D(boundary::geometry) AS b FROM cities WHERE code = :code) c"
            ),
            {"code": city_code},
        )
    ).first()
    if row is None:
        raise ValueError(f"city {city_code} is not seeded; run `python -m app.cli seed`")
    bbox: tuple[float, float, float, float] | None = None
    if row[1] is not None:
        bbox = (float(row[1]), float(row[2]), float(row[3]), float(row[4]))
    return CityContext(id=row[0], code=city_code, bbox=bbox)


async def inside_city(session: AsyncSession, city_id: uuid.UUID, lng: float, lat: float) -> bool:
    """``ST_Covers(cities.boundary, point)``; a city without a boundary covers nothing."""
    covered = await session.scalar(
        select(
            func.ST_Covers(
                City.__table__.c.boundary,
                func.ST_GeogFromText(ewkt_point(lng, lat)),
            )
        ).where(City.id == city_id)
    )
    return bool(covered)


# ---- Import runs --------------------------------------------------------------------------


@dataclass
class RunReport:
    provider_key: str
    skipped_unchanged: bool = False
    import_run_id: uuid.UUID | None = None
    record_count: int = 0
    accepted: int = 0
    rejected: int = 0
    skipped: int = 0
    created_places: int = 0
    rejection_reasons: dict[str, int] = field(default_factory=dict)

    def reject(self, reason: str) -> None:
        self.rejected += 1
        self.rejection_reasons[reason] = self.rejection_reasons.get(reason, 0) + 1


async def start_run(
    session: AsyncSession,
    policy: ActivePolicy,
    city_id: uuid.UUID,
    *,
    release_id: str,
    checksum: str,
    importer_version: str,
) -> ImportRun | None:
    """Open a RUNNING run, or return None when the identical release already SUCCEEDED."""
    existing = await session.scalar(
        select(ImportRun.id).where(
            ImportRun.data_provider_id == policy.provider_id,
            ImportRun.city_id == city_id,
            ImportRun.release_id == release_id,
            ImportRun.checksum_sha256 == checksum,
            ImportRun.importer_version == importer_version,
            ImportRun.status == "SUCCEEDED",
        )
    )
    if existing is not None:
        return None
    run = ImportRun(
        data_provider_id=policy.provider_id,
        provider_policy_id=policy.policy_id,
        city_id=city_id,
        release_id=release_id,
        checksum_sha256=checksum,
        importer_version=importer_version,
        status="RUNNING",
        # Wall clock, not now(): runs inside one transaction must still order (latest record wins).
        started_at=datetime.now(UTC),
    )
    session.add(run)
    await session.flush()
    return run


def finish_run(run: ImportRun, report: RunReport) -> None:
    run.status = "SUCCEEDED"
    run.completed_at = datetime.now(UTC)
    run.record_count = report.record_count
    run.accepted_count = report.accepted
    run.rejected_count = report.rejected
    run.duplicate_count = report.skipped


def add_record(
    session: AsyncSession,
    run: ImportRun,
    *,
    upstream_id: str,
    raw_name: str,
    upstream_category: str | None,
    lng: float,
    lat: float,
    payload: Mapping[str, Any],
    rejection_reason: str | None = None,
    place_id: uuid.UUID | None = None,
    match_state: str = "UNMATCHED",
) -> ImportRecord:
    record = ImportRecord(
        import_run_id=run.id,
        upstream_id=upstream_id,
        raw_name=raw_name or upstream_id,
        normalized_name=(normalize_search_text(raw_name) or upstream_id.lower()).lower(),
        upstream_category=upstream_category,
        location=ewkt_point(lng, lat),
        allowed_payload=dict(payload),
        validation_status="REJECTED" if rejection_reason else "ACCEPTED",
        rejection_reason=rejection_reason,
        match_state=match_state,
        place_id=place_id,
    )
    session.add(record)
    return record


# ---- Places and identities ----------------------------------------------------------------


async def place_for_identity(
    session: AsyncSession, provider_id: uuid.UUID, upstream_id: str
) -> uuid.UUID | None:
    return await session.scalar(
        select(ExternalPlaceIdentity.place_id).where(
            ExternalPlaceIdentity.data_provider_id == provider_id,
            ExternalPlaceIdentity.upstream_id == upstream_id,
        )
    )


async def free_slug(session: AsyncSession, city_id: uuid.UUID, name: str) -> str:
    base = slugify(name)
    candidate = base
    suffix = 2
    while await session.scalar(
        select(Place.id).where(Place.city_id == city_id, Place.slug == candidate)
    ):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


async def create_place(
    session: AsyncSession,
    *,
    city_id: uuid.UUID,
    slug: str,
    lng: float,
    lat: float,
    category_code: str | None,
    area_code: str | None,
) -> Place:
    """A new candidate place (workflow IMPORTED, i.e. draft until the gate publishes it)."""
    place = Place(
        city_id=city_id,
        slug=slug,
        location=ewkt_point(lng, lat),
        category_code=category_code,
        area_code=area_code,
        workflow_state="IMPORTED",
        has_no_media=True,
    )
    session.add(place)
    await session.flush()
    return place


async def link_identity(
    session: AsyncSession,
    *,
    place_id: uuid.UUID,
    provider_id: uuid.UUID,
    upstream_id: str,
    release: str | None,
    match_method: str = "EXACT_ID",
) -> None:
    existing = await session.scalar(
        select(ExternalPlaceIdentity).where(
            ExternalPlaceIdentity.data_provider_id == provider_id,
            ExternalPlaceIdentity.upstream_id == upstream_id,
        )
    )
    if existing is None:
        session.add(
            ExternalPlaceIdentity(
                place_id=place_id,
                data_provider_id=provider_id,
                upstream_id=upstream_id,
                upstream_release=release,
                match_method=match_method,
                review_state="PENDING",
            )
        )
    elif existing.upstream_release != release:
        existing.upstream_release = release


# ---- Sources ------------------------------------------------------------------------------


async def get_or_create_source(
    session: AsyncSession,
    *,
    data_provider_id: uuid.UUID | None,
    publisher: str,
    source_kind: str,
    license_code: str,
    attribution_text: str | None,
    homepage_url: str | None = None,
) -> Source:
    source = await session.scalar(
        select(Source)
        .where(
            Source.publisher == publisher,
            Source.license_code == license_code,
            Source.source_kind == source_kind,
            Source.data_provider_id.is_(None)
            if data_provider_id is None
            else Source.data_provider_id == data_provider_id,
        )
        .order_by(Source.created_at)
        .limit(1)
    )
    if source is None:
        source = Source(
            data_provider_id=data_provider_id,
            publisher=publisher,
            source_kind=source_kind,
            homepage_url=homepage_url,
            license_code=license_code,
            attribution_text=attribution_text,
        )
        session.add(source)
        await session.flush()
    else:
        if source.attribution_text != attribution_text:
            source.attribution_text = attribution_text
        if homepage_url and source.homepage_url != homepage_url:
            source.homepage_url = homepage_url
    return source


async def get_or_create_revision(
    session: AsyncSession,
    *,
    source_id: uuid.UUID,
    locator: str,
    content_sha256: str,
    title: str | None,
    retrieved_at: datetime | None = None,
) -> SourceRevision:
    """Reuse the newest revision of ``locator`` with the same content hash, else append one."""
    latest = await session.scalar(
        select(SourceRevision)
        .where(
            SourceRevision.source_id == source_id,
            SourceRevision.locator == locator,
            SourceRevision.content_sha256 == content_sha256,
        )
        .order_by(SourceRevision.retrieved_at.desc())
        .limit(1)
    )
    if latest is not None:
        return latest
    revision = SourceRevision(
        source_id=source_id,
        locator=locator,
        title=title,
        retrieved_at=retrieved_at or datetime.now(UTC),
        content_sha256=content_sha256,
    )
    session.add(revision)
    await session.flush()
    return revision

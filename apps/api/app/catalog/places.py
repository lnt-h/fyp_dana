"""Published-place reads (FR-003..FR-008, FR-051): summaries, detail, facts, media, closure rules.

Only places with a current ``PUBLISHED`` catalog publication are visible (FR-004); every query goes
through ``vw_published_places`` (same predicate as the planner pool, Q-P1). Facts come from the
publication snapshot (``vw_published_place_facts``), never from drafts. Unknown facts stay
``UNKNOWN``; nothing here fills a missing value.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    Select,
    SmallInteger,
    Text,
    and_,
    column,
    func,
    or_,
    select,
    table,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.reference import AreaRecord
from app.models.catalog import (
    CatalogPublication,
    FactEvidence,
    MediaAsset,
    Place,
    PlaceClosureRule,
    PlaceMedia,
    PublicationMedia,
    Source,
    SourceRevision,
)
from app.models.reference import Area

# Read-only views from migration 0002 (no ORM model; raw geography columns, not EWKT).
vw_published_places = table(
    "vw_published_places",
    column("catalog_publication_id", UUID(as_uuid=True)),
    column("place_id", UUID(as_uuid=True)),
    column("city_id", UUID(as_uuid=True)),
    column("publication_revision", Integer),
    column("category_code", Text),
    column("name_vi", Text),
    column("name_en", Text),
    column("short_description_vi", Text),
    column("short_description_en", Text),
    column("description_vi", Text),
    column("description_en", Text),
    column("location"),
    column("entrance_location"),
    column("visit_minutes_min", SmallInteger),
    column("visit_minutes_suggested", SmallInteger),
    column("visit_minutes_max", SmallInteger),
    column("corpus_revision", Integer),
    column("published_at", DateTime(timezone=True)),
)

vw_published_place_facts = table(
    "vw_published_place_facts",
    column("place_id", UUID(as_uuid=True)),
    column("catalog_publication_id", UUID(as_uuid=True)),
    column("place_fact_id", UUID(as_uuid=True)),
    column("field_code", Text),
    column("is_operational", Boolean),
    column("knowledge_state", Text),
    column("value", JSONB),
    column("verified_at", DateTime(timezone=True)),
    column("valid_until", Date),
    column("is_stale", Boolean),
)

@dataclass(frozen=True)
class MediaRecord:
    media_asset_id: uuid.UUID
    object_key: str
    width_px: int
    height_px: int
    creator: str
    license_code: str
    attribution_text: str
    alt_text_vi: str | None
    alt_text_en: str | None
    ordinal: int


@dataclass(frozen=True)
class PlaceSummaryRecord:
    place_id: uuid.UUID
    catalog_publication_id: uuid.UUID
    city_id: uuid.UUID
    slug: str
    category_code: str
    area_code: str | None
    name_vi: str
    name_en: str
    short_description_vi: str | None
    short_description_en: str | None
    lat: float
    lng: float
    visit_minutes_suggested: int
    thumbnail: MediaRecord | None = None
    # Published places are always VERIFIED (architecture §5 trust label contract).
    trust_level: Literal["VERIFIED"] = "VERIFIED"

    def name(self, locale: str) -> str:
        return self.name_en if locale == "en" else self.name_vi

    def short_description(self, locale: str) -> str | None:
        return self.short_description_en if locale == "en" else self.short_description_vi


@dataclass(frozen=True)
class FactSourceRecord:
    source_revision_id: uuid.UUID
    publisher: str
    title: str | None
    locator: str
    retrieved_at: datetime
    license_code: str
    attribution_text: str | None
    homepage_url: str | None


@dataclass(frozen=True)
class FactRecord:
    place_fact_id: uuid.UUID
    field_code: str
    is_operational: bool
    knowledge_state: str
    value: dict[str, Any] | None
    verified_at: datetime | None
    valid_until: date | None
    is_stale: bool
    sources: tuple[FactSourceRecord, ...]


@dataclass(frozen=True)
class ClosureRuleRecord:
    id: uuid.UUID
    applies_to: str
    rule_kind: str
    effect: str
    severity: str
    params: dict[str, Any]
    note_vi: str
    note_en: str
    effective_from: date | None
    effective_to: date | None
    verified_at: datetime | None


@dataclass(frozen=True)
class PlaceDetailRecord:
    summary: PlaceSummaryRecord
    publication_revision: int
    published_at: datetime
    description_vi: str | None
    description_en: str | None
    visit_minutes_min: int
    visit_minutes_max: int
    entrance_lat: float | None
    entrance_lng: float | None
    area: AreaRecord | None
    facts: tuple[FactRecord, ...]
    media: tuple[MediaRecord, ...]
    closure_rules: tuple[ClosureRuleRecord, ...]


def _lat(geography: Any) -> Any:
    return func.ST_Y(func.geometry(geography), type_=Float)


def _lng(geography: Any) -> Any:
    return func.ST_X(func.geometry(geography), type_=Float)


def published_places_select() -> Select[Any]:
    """Columns of :class:`PlaceSummaryRecord` over the published view (+ slug, area_code)."""
    vw = vw_published_places
    return (
        select(
            vw.c.place_id,
            vw.c.catalog_publication_id,
            vw.c.city_id,
            Place.slug,
            vw.c.category_code,
            CatalogPublication.area_code,
            vw.c.name_vi,
            vw.c.name_en,
            vw.c.short_description_vi,
            vw.c.short_description_en,
            _lat(vw.c.location).label("lat"),
            _lng(vw.c.location).label("lng"),
            vw.c.visit_minutes_suggested,
        )
        .select_from(vw)
        .join(CatalogPublication, CatalogPublication.id == vw.c.catalog_publication_id)
        .join(Place, Place.id == vw.c.place_id)
    )


def summary_from_row(row: Any, thumbnail: MediaRecord | None = None) -> PlaceSummaryRecord:
    return PlaceSummaryRecord(
        place_id=row.place_id,
        catalog_publication_id=row.catalog_publication_id,
        city_id=row.city_id,
        slug=row.slug,
        category_code=row.category_code,
        area_code=row.area_code,
        name_vi=row.name_vi,
        name_en=row.name_en,
        short_description_vi=row.short_description_vi,
        short_description_en=row.short_description_en,
        lat=row.lat,
        lng=row.lng,
        visit_minutes_suggested=row.visit_minutes_suggested,
        thumbnail=thumbnail,
    )


async def load_publication_media(
    session: AsyncSession, publication_ids: Sequence[uuid.UUID]
) -> dict[uuid.UUID, list[MediaRecord]]:
    """Media of each publication in ordinal order; only rights still CLEARED and unexpired."""
    if not publication_ids:
        return {}
    rows = (
        await session.execute(
            select(
                PublicationMedia.catalog_publication_id,
                PublicationMedia.ordinal,
                MediaAsset.id,
                MediaAsset.object_key,
                MediaAsset.width_px,
                MediaAsset.height_px,
                MediaAsset.creator,
                MediaAsset.license_code,
                MediaAsset.attribution_text,
                PlaceMedia.alt_text_vi,
                PlaceMedia.alt_text_en,
            )
            .join(MediaAsset, MediaAsset.id == PublicationMedia.media_asset_id)
            .join(
                CatalogPublication,
                CatalogPublication.id == PublicationMedia.catalog_publication_id,
            )
            .outerjoin(
                PlaceMedia,
                and_(
                    PlaceMedia.place_id == CatalogPublication.place_id,
                    PlaceMedia.media_asset_id == MediaAsset.id,
                ),
            )
            .where(
                PublicationMedia.catalog_publication_id.in_(publication_ids),
                MediaAsset.rights_state == "CLEARED",
                or_(
                    MediaAsset.rights_expires_on.is_(None),
                    MediaAsset.rights_expires_on > func.current_date(),
                ),
            )
            .order_by(PublicationMedia.catalog_publication_id, PublicationMedia.ordinal)
        )
    ).all()
    media: dict[uuid.UUID, list[MediaRecord]] = {}
    for row in rows:
        media.setdefault(row.catalog_publication_id, []).append(
            MediaRecord(
                media_asset_id=row.id,
                object_key=row.object_key,
                width_px=row.width_px,
                height_px=row.height_px,
                creator=row.creator,
                license_code=row.license_code,
                attribution_text=row.attribution_text,
                alt_text_vi=row.alt_text_vi,
                alt_text_en=row.alt_text_en,
                ordinal=row.ordinal,
            )
        )
    return media


async def attach_thumbnails(
    session: AsyncSession, rows: Sequence[Any]
) -> list[PlaceSummaryRecord]:
    media = await load_publication_media(session, [row.catalog_publication_id for row in rows])
    records = []
    for row in rows:
        items = media.get(row.catalog_publication_id)
        records.append(summary_from_row(row, items[0] if items else None))
    return records


class PlacesRepository:
    """Published places of the catalog. Candidates (unpublished places) are never returned."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_published(
        self,
        city_id: uuid.UUID,
        *,
        category_codes: Sequence[str] | None = None,
        area_codes: Sequence[str] | None = None,
        place_ids: Sequence[uuid.UUID] | None = None,
    ) -> list[PlaceSummaryRecord]:
        """Unpaginated pool of published places of a city (planner candidates, Q-P1)."""
        stmt = published_places_select().where(vw_published_places.c.city_id == city_id)
        if category_codes:
            stmt = stmt.where(vw_published_places.c.category_code.in_(list(category_codes)))
        if area_codes:
            stmt = stmt.where(CatalogPublication.area_code.in_(list(area_codes)))
        if place_ids is not None:
            stmt = stmt.where(vw_published_places.c.place_id.in_(list(place_ids)))
        rows = (await self._session.execute(stmt.order_by(vw_published_places.c.place_id))).all()
        return await attach_thumbnails(self._session, rows)

    async def get_published_detail(self, place_id: uuid.UUID) -> PlaceDetailRecord | None:
        vw = vw_published_places
        row = (
            await self._session.execute(
                published_places_select()
                .add_columns(
                    vw.c.publication_revision,
                    vw.c.published_at,
                    vw.c.description_vi,
                    vw.c.description_en,
                    vw.c.visit_minutes_min,
                    vw.c.visit_minutes_max,
                    _lat(vw.c.entrance_location).label("entrance_lat"),
                    _lng(vw.c.entrance_location).label("entrance_lng"),
                    Area.name_vi.label("area_name_vi"),
                    Area.name_en.label("area_name_en"),
                    Area.sort_order.label("area_sort_order"),
                )
                .outerjoin(
                    Area,
                    and_(
                        Area.code == CatalogPublication.area_code,
                        Area.city_id == CatalogPublication.city_id,
                    ),
                )
                .where(vw.c.place_id == place_id)
            )
        ).one_or_none()
        if row is None:
            return None
        media = (await load_publication_media(self._session, [row.catalog_publication_id])).get(
            row.catalog_publication_id, []
        )
        area = (
            AreaRecord(
                code=row.area_code,
                city_id=row.city_id,
                name_vi=row.area_name_vi,
                name_en=row.area_name_en,
                sort_order=row.area_sort_order,
            )
            if row.area_code is not None and row.area_name_vi is not None
            else None
        )
        return PlaceDetailRecord(
            summary=summary_from_row(row, media[0] if media else None),
            publication_revision=row.publication_revision,
            published_at=row.published_at,
            description_vi=row.description_vi,
            description_en=row.description_en,
            visit_minutes_min=row.visit_minutes_min,
            visit_minutes_max=row.visit_minutes_max,
            entrance_lat=row.entrance_lat,
            entrance_lng=row.entrance_lng,
            area=area,
            facts=tuple(await self.list_published_facts(place_id)),
            media=tuple(media),
            closure_rules=tuple(
                await self.list_closure_rules(
                    city_id=row.city_id, place_id=place_id, area_code=row.area_code
                )
            ),
        )

    async def list_published_facts(self, place_id: uuid.UUID) -> list[FactRecord]:
        """Facts of the current publication with their sources, ordered by field code."""
        vf = vw_published_place_facts
        fact_rows = (
            await self._session.execute(
                select(
                    vf.c.place_fact_id,
                    vf.c.field_code,
                    vf.c.is_operational,
                    vf.c.knowledge_state,
                    vf.c.value,
                    vf.c.verified_at,
                    vf.c.valid_until,
                    vf.c.is_stale,
                )
                .where(vf.c.place_id == place_id)
                .order_by(vf.c.field_code)
            )
        ).all()
        fact_ids = [row.place_fact_id for row in fact_rows]
        sources: dict[uuid.UUID, list[FactSourceRecord]] = {}
        if fact_ids:
            source_rows = (
                await self._session.execute(
                    select(
                        FactEvidence.place_fact_id,
                        SourceRevision.id,
                        Source.publisher,
                        SourceRevision.title,
                        SourceRevision.locator,
                        SourceRevision.retrieved_at,
                        Source.license_code,
                        Source.attribution_text,
                        Source.homepage_url,
                    )
                    .join(SourceRevision, SourceRevision.id == FactEvidence.source_revision_id)
                    .join(Source, Source.id == SourceRevision.source_id)
                    .where(FactEvidence.place_fact_id.in_(fact_ids))
                    .order_by(
                        FactEvidence.place_fact_id,
                        SourceRevision.retrieved_at.desc(),
                        SourceRevision.id,
                    )
                )
            ).all()
            for source in source_rows:
                sources.setdefault(source.place_fact_id, []).append(
                    FactSourceRecord(
                        source_revision_id=source.id,
                        publisher=source.publisher,
                        title=source.title,
                        locator=source.locator,
                        retrieved_at=source.retrieved_at,
                        license_code=source.license_code,
                        attribution_text=source.attribution_text,
                        homepage_url=source.homepage_url,
                    )
                )
        return [
            FactRecord(
                place_fact_id=row.place_fact_id,
                field_code=row.field_code,
                is_operational=row.is_operational,
                knowledge_state=row.knowledge_state,
                value=row.value,
                verified_at=row.verified_at,
                valid_until=row.valid_until,
                is_stale=bool(row.is_stale),
                sources=tuple(sources.get(row.place_fact_id, ())),
            )
            for row in fact_rows
        ]

    async def list_closure_rules(
        self, *, city_id: uuid.UUID, place_id: uuid.UUID, area_code: str | None
    ) -> list[ClosureRuleRecord]:
        """Approved, not yet ended closure rules applying to the place, its area or its city."""
        rule = PlaceClosureRule
        scope = or_(
            and_(rule.applies_to == "PLACE", rule.place_id == place_id),
            and_(rule.applies_to == "CITY"),
        )
        if area_code is not None:
            scope = or_(scope, and_(rule.applies_to == "AREA", rule.area_code == area_code))
        rows = (
            await self._session.execute(
                select(rule)
                .where(
                    rule.city_id == city_id,
                    rule.review_state == "APPROVED",
                    or_(rule.effective_to.is_(None), rule.effective_to >= func.current_date()),
                    scope,
                )
                .order_by(rule.applies_to, rule.rule_kind, rule.id)
            )
        ).scalars()
        return [
            ClosureRuleRecord(
                id=r.id,
                applies_to=r.applies_to,
                rule_kind=r.rule_kind,
                effect=r.effect,
                severity=r.severity,
                params=r.params,
                note_vi=r.note_vi,
                note_en=r.note_en,
                effective_from=r.effective_from,
                effective_to=r.effective_to,
                verified_at=r.verified_at,
            )
            for r in rows
        ]

"""Sources and source revisions (FR-016), import runs (read-only, ADR-012), city summary."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import (
    audit,
    clamp_limit,
    commit,
    decode_cursor,
    flush,
    page_slice,
)
from app.errors import invalid, not_found
from app.models.catalog import CatalogPublication, Place, Source, SourceRevision, WebPlaceCandidate
from app.models.providers import DataProvider, ImportRun
from app.models.reference import City
from app.schemas.admin import (
    AreaCount,
    CitySummary,
    CitySummaryList,
    ImportRunPage,
    SourceCreate,
    SourcePage,
    SourceRevisionCreate,
    SourceRevisionList,
)
from app.schemas.admin import ImportRun as ImportRunSchema
from app.schemas.admin import Source as SourceSchema
from app.schemas.admin import SourceRevision as SourceRevisionSchema


class CatalogAdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ---- sources ------------------------------------------------------------------------

    async def list_sources(
        self, *, cursor: str | None = None, limit: int | None = None
    ) -> SourcePage:
        offset = decode_cursor(cursor)
        size = clamp_limit(limit)
        rows = (
            await self._session.scalars(
                select(Source).order_by(Source.publisher, Source.id).offset(offset).limit(size + 1)
            )
        ).all()
        page, next_cursor = page_slice(rows, offset, size)
        return SourcePage(
            next_cursor=next_cursor,
            items=[SourceSchema.model_validate(row, from_attributes=True) for row in page],
        )

    async def get_source(self, source_id: uuid.UUID) -> SourceSchema:
        row = await self._session.get(Source, source_id)
        if row is None:
            raise not_found("Source not found")
        return SourceSchema.model_validate(row, from_attributes=True)

    async def create_source(self, data: SourceCreate, actor_account_id: uuid.UUID) -> SourceSchema:
        if data.data_provider_id is not None and (
            await self._session.get(DataProvider, data.data_provider_id) is None
        ):
            raise invalid("unknown_data_provider", "Unknown data provider")
        row = Source(
            data_provider_id=data.data_provider_id,
            publisher=data.publisher,
            source_kind=data.source_kind,
            homepage_url=data.homepage_url,
            license_code=data.license_code,
            attribution_text=data.attribution_text,
        )
        self._session.add(row)
        await flush(self._session)
        audit(
            self._session,
            actor_account_id=actor_account_id,
            entity_table="sources",
            entity_id=row.id,
            action="CONTENT_REVIEW",
            detail={"operation": "create", "source_kind": row.source_kind},
        )
        await commit(self._session)
        await self._session.refresh(row)
        return SourceSchema.model_validate(row, from_attributes=True)

    async def list_source_revisions(self, source_id: uuid.UUID) -> SourceRevisionList:
        await self.get_source(source_id)
        rows = (
            await self._session.scalars(
                select(SourceRevision)
                .where(SourceRevision.source_id == source_id)
                .order_by(SourceRevision.retrieved_at.desc(), SourceRevision.id)
            )
        ).all()
        return SourceRevisionList(
            items=[SourceRevisionSchema.model_validate(row, from_attributes=True) for row in rows]
        )

    async def create_source_revision(
        self, source_id: uuid.UUID, data: SourceRevisionCreate, actor_account_id: uuid.UUID
    ) -> SourceRevisionSchema:
        await self.get_source(source_id)
        row = SourceRevision(
            source_id=source_id,
            locator=data.locator,
            title=data.title,
            retrieved_at=data.retrieved_at,
            content_sha256=data.content_sha256,
        )
        self._session.add(row)
        await flush(self._session)
        audit(
            self._session,
            actor_account_id=actor_account_id,
            entity_table="source_revisions",
            entity_id=row.id,
            action="CONTENT_REVIEW",
            detail={"operation": "create", "source_id": str(source_id)},
        )
        await commit(self._session)
        await self._session.refresh(row)
        return SourceRevisionSchema.model_validate(row, from_attributes=True)

    # ---- imports ------------------------------------------------------------------------

    async def list_import_runs(
        self,
        *,
        city_id: uuid.UUID | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> ImportRunPage:
        offset = decode_cursor(cursor)
        size = clamp_limit(limit)
        statement = select(ImportRun, DataProvider.provider_key).join(
            DataProvider, DataProvider.id == ImportRun.data_provider_id
        )
        if city_id is not None:
            statement = statement.where(ImportRun.city_id == city_id)
        rows = (
            await self._session.execute(
                statement.order_by(ImportRun.started_at.desc(), ImportRun.id)
                .offset(offset)
                .limit(size + 1)
            )
        ).all()
        page, next_cursor = page_slice(rows, offset, size)
        return ImportRunPage(
            next_cursor=next_cursor, items=[_import_run(run, key) for run, key in page]
        )

    async def get_import_run(self, import_run_id: uuid.UUID) -> ImportRunSchema:
        row = (
            await self._session.execute(
                select(ImportRun, DataProvider.provider_key)
                .join(DataProvider, DataProvider.id == ImportRun.data_provider_id)
                .where(ImportRun.id == import_run_id)
            )
        ).first()
        if row is None:
            raise not_found("Import run not found")
        return _import_run(row[0], row[1])

    # ---- city summary -------------------------------------------------------------------

    async def _counts(self, statement: Any) -> dict[uuid.UUID, int]:
        rows = (await self._session.execute(statement)).all()
        return {row[0]: int(row[1]) for row in rows}

    async def city_summary(self) -> CitySummaryList:
        cities = (await self._session.scalars(select(City).order_by(City.code))).all()
        published = await self._counts(
            select(CatalogPublication.city_id, func.count())
            .where(CatalogPublication.state == "PUBLISHED")
            .group_by(CatalogPublication.city_id)
        )
        candidates = await self._counts(
            select(Place.city_id, func.count())
            .where(Place.workflow_state.not_in(("PUBLISHED", "RETIRED")))
            .group_by(Place.city_id)
        )
        pending_web = await self._counts(
            select(WebPlaceCandidate.city_id, func.count())
            .where(WebPlaceCandidate.review_state == "PENDING")
            .group_by(WebPlaceCandidate.city_id)
        )
        by_area: dict[uuid.UUID, list[AreaCount]] = {}
        area_rows = (
            await self._session.execute(
                select(CatalogPublication.city_id, CatalogPublication.area_code, func.count())
                .where(
                    CatalogPublication.state == "PUBLISHED",
                    CatalogPublication.area_code.is_not(None),
                )
                .group_by(CatalogPublication.city_id, CatalogPublication.area_code)
                .order_by(CatalogPublication.area_code)
            )
        ).all()
        for city_id, area_code, count in area_rows:
            by_area.setdefault(city_id, []).append(
                AreaCount(area_code=area_code, published_count=count)
            )
        return CitySummaryList(
            items=[
                CitySummary(
                    city_id=city.id,
                    code=city.code,
                    is_enabled=city.is_enabled,
                    published_count=published.get(city.id, 0),
                    candidate_count=candidates.get(city.id, 0),
                    pending_web_candidate_count=pending_web.get(city.id, 0),
                    published_by_area=by_area.get(city.id, []),
                )
                for city in cities
            ]
        )


def _import_run(run: ImportRun, provider_key: str | None) -> ImportRunSchema:
    schema = ImportRunSchema.model_validate(run, from_attributes=True)
    return schema.model_copy(update={"provider_key": provider_key})

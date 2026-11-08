"""Operator surfaces kept by DEC-022: emergency takedown and the release-gate city summary."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import commit, get_place
from app.errors import conflict
from app.models.catalog import CatalogPublication, Place, WebPlaceCandidate
from app.models.reference import City
from app.schemas.admin import AreaCount, CitySummary, CitySummaryList, UnpublishRequest
from app.schemas.admin import CatalogPublication as CatalogPublicationSchema


class OperatorService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def unpublish(
        self, place_id: uuid.UUID, data: UnpublishRequest, actor_account_id: uuid.UUID
    ) -> CatalogPublicationSchema:
        """Withdraw the current publication (FR-017). The pipeline never re-publishes a
        WITHDRAWN place on its own (``auto_publish``'s ``include_withdrawn`` is opt-in)."""
        await get_place(self._session, place_id, lock=True)
        current = await self._session.scalar(
            select(CatalogPublication).where(
                CatalogPublication.place_id == place_id, CatalogPublication.state == "PUBLISHED"
            )
        )
        if current is None:
            raise conflict("not_published", "The place has no current publication")
        await self._session.execute(
            select(func.fn_withdraw_place(place_id, actor_account_id, data.state_reason))
        )
        await commit(self._session)
        row = await self._session.get(CatalogPublication, current.id, populate_existing=True)
        assert row is not None
        return CatalogPublicationSchema.model_validate(row, from_attributes=True)

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


async def takedown_place(
    session: AsyncSession,
    *,
    city_id: uuid.UUID,
    slug: str,
    reason: str,
    actor_account_id: uuid.UUID,
    retire: bool = True,
) -> tuple[uuid.UUID, bool, bool]:
    """Owner takedown by slug (CLI ``publish takedown``): withdraw the current publication if
    any (``fn_withdraw_place``, audited) and, with ``retire``, mark the place RETIRED so the
    pipeline never re-publishes or re-matches it. Returns ``(place_id, withdrawn, retired)``.
    Commits; raises ``LookupError`` for an unknown slug."""
    place = await session.scalar(
        select(Place).where(Place.city_id == city_id, Place.slug == slug).with_for_update()
    )
    if place is None:
        raise LookupError(f"no place with slug {slug!r} in this city")
    published = await session.scalar(
        select(CatalogPublication.id).where(
            CatalogPublication.place_id == place.id, CatalogPublication.state == "PUBLISHED"
        )
    )
    if published is not None:
        await session.execute(select(func.fn_withdraw_place(place.id, actor_account_id, reason)))
    retired = False
    if retire and place.workflow_state != "RETIRED":
        await session.execute(
            update(Place).where(Place.id == place.id).values(workflow_state="RETIRED")
        )
        retired = True
    await session.commit()
    return place.id, published is not None, retired

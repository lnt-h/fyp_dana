"""Reference data reads: enabled cities, travel areas and categories (FR-001, FR-003)."""

import uuid
from dataclasses import dataclass

from sqlalchemy import Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference import Area, Category, City


@dataclass(frozen=True)
class AreaRecord:
    code: str
    city_id: uuid.UUID
    name_vi: str
    name_en: str
    sort_order: int


@dataclass(frozen=True)
class CityRecord:
    id: uuid.UUID
    code: str
    name_vi: str
    name_en: str
    time_zone: str
    centre_lat: float | None
    centre_lng: float | None
    areas: tuple[AreaRecord, ...]


@dataclass(frozen=True)
class CategoryRecord:
    code: str
    name_vi: str
    name_en: str
    sort_order: int


def normalize_category_code(code: str) -> str:
    """Category codes are UPPER_CASE in the schema; accept lower-case input (mobile fixtures)."""
    return code.strip().upper()


class ReferenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_enabled_cities(self) -> list[CityRecord]:
        centroid = func.ST_Centroid(func.geometry(City.boundary))
        rows = (
            await self._session.execute(
                select(
                    City.id,
                    City.code,
                    City.name_vi,
                    City.name_en,
                    City.time_zone,
                    func.ST_Y(centroid, type_=Float).label("centre_lat"),
                    func.ST_X(centroid, type_=Float).label("centre_lng"),
                )
                .where(City.is_enabled.is_(True))
                .order_by(City.code)
            )
        ).all()
        areas = await self.list_areas([row.id for row in rows])
        return [
            CityRecord(
                id=row.id,
                code=row.code,
                name_vi=row.name_vi,
                name_en=row.name_en,
                time_zone=row.time_zone,
                centre_lat=row.centre_lat,
                centre_lng=row.centre_lng,
                areas=tuple(area for area in areas if area.city_id == row.id),
            )
            for row in rows
        ]

    async def get_enabled_city(
        self, *, city_id: uuid.UUID | None = None, city_code: str | None = None
    ) -> CityRecord | None:
        """The enabled city matching ``city_id`` or ``city_code``; None if unknown or disabled."""
        for city in await self.list_enabled_cities():
            if (city_id is None or city.id == city_id) and (
                city_code is None or city.code == city_code
            ):
                return city
        return None

    async def list_areas(self, city_ids: list[uuid.UUID]) -> list[AreaRecord]:
        if not city_ids:
            return []
        rows = (
            await self._session.execute(
                select(Area.code, Area.city_id, Area.name_vi, Area.name_en, Area.sort_order)
                .where(Area.city_id.in_(city_ids))
                .order_by(Area.sort_order, Area.code)
            )
        ).all()
        return [
            AreaRecord(
                code=row.code,
                city_id=row.city_id,
                name_vi=row.name_vi,
                name_en=row.name_en,
                sort_order=row.sort_order,
            )
            for row in rows
        ]

    async def list_categories(self) -> list[CategoryRecord]:
        rows = (
            await self._session.execute(
                select(
                    Category.code, Category.name_vi, Category.name_en, Category.sort_order
                ).order_by(Category.sort_order, Category.code)
            )
        ).all()
        return [
            CategoryRecord(
                code=row.code, name_vi=row.name_vi, name_en=row.name_en, sort_order=row.sort_order
            )
            for row in rows
        ]

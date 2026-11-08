"""Travel-area polygons and point-in-polygon assignment (pure Python, DEC-022).

``data/areas/<city>.yaml`` is the owner-maintained source. Assignment is first match in file
order; ``write_area_boundaries`` copies the polygons into ``areas.boundary`` for SQL users and
creates (or renames) an area that carries ``name_vi`` / ``name_en`` in the YAML. Areas marked
``hoi_an_area: true`` form the "Hội An area" group of the release gate.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference import Area, City

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
AREAS_DIR = DATA_DIR / "areas"

Ring = tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class AreaPolygon:
    code: str
    ring: Ring  # closed: first point == last point; (lng, lat)
    name_vi: str | None = None
    name_en: str | None = None
    hoi_an_area: bool = False
    # Short display names used to tell apart places sharing one name ("Chùa Linh Ứng (Bãi Bụt)").
    short_vi: str | None = None
    short_en: str | None = None

    def contains(self, lng: float, lat: float) -> bool:
        return point_in_ring(lng, lat, self.ring)

    def ewkt(self) -> str:
        coords = ", ".join(f"{x} {y}" for x, y in self.ring)
        return f"SRID=4326;MULTIPOLYGON((({coords})))"


def point_in_ring(lng: float, lat: float, ring: Sequence[tuple[float, float]]) -> bool:
    """Even-odd ray casting; points on an edge count as inside."""
    inside = False
    count = len(ring)
    for index in range(count - 1):
        x1, y1 = ring[index]
        x2, y2 = ring[index + 1]
        if _on_segment(lng, lat, x1, y1, x2, y2):
            return True
        if (y1 > lat) != (y2 > lat):
            x_cross = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lng < x_cross:
                inside = not inside
    return inside


def _on_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> bool:
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if abs(cross) > 1e-12:
        return False
    return min(x1, x2) - 1e-12 <= px <= max(x1, x2) + 1e-12 and (
        min(y1, y2) - 1e-12 <= py <= max(y1, y2) + 1e-12
    )


def parse_areas(document: dict[str, Any]) -> tuple[AreaPolygon, ...]:
    areas: list[AreaPolygon] = []
    seen: set[str] = set()
    for item in document.get("areas") or []:
        code = str(item["code"])
        if code in seen:
            raise ValueError(f"duplicate area code {code}")
        seen.add(code)
        points = [(float(lng), float(lat)) for lng, lat in item["polygon"]]
        if len(points) < 3:
            raise ValueError(f"area {code} needs at least three points")
        for lng, lat in points:
            if not (-180 <= lng <= 180 and -90 <= lat <= 90):
                raise ValueError(f"area {code} has an invalid coordinate")
        if points[0] != points[-1]:
            points.append(points[0])
        name_vi = str(item.get("name_vi") or "").strip() or None
        name_en = str(item.get("name_en") or "").strip() or None
        areas.append(
            AreaPolygon(
                code=code,
                ring=tuple(points),
                name_vi=name_vi,
                name_en=name_en,
                hoi_an_area=bool(item.get("hoi_an_area", False)),
                short_vi=str(item.get("short_vi") or "").strip() or None,
                short_en=str(item.get("short_en") or "").strip() or None,
            )
        )
    return tuple(areas)


def hoi_an_area_codes(areas: Sequence[AreaPolygon]) -> frozenset[str]:
    """Codes of the areas grouped as "the Hội An area" (release gate: ≥ 30 published)."""
    return frozenset(area.code for area in areas if area.hoi_an_area)


@lru_cache(maxsize=8)
def load_areas(city_code: str, directory: Path = AREAS_DIR) -> tuple[AreaPolygon, ...]:
    path = directory / f"{city_code}.yaml"
    if not path.exists():
        return ()
    document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return parse_areas(document)


def assign_area(areas: Sequence[AreaPolygon], lng: float, lat: float) -> str | None:
    for area in areas:
        if area.contains(lng, lat):
            return area.code
    return None


async def write_area_boundaries(
    session: AsyncSession, city_code: str, areas: Sequence[AreaPolygon] | None = None
) -> int:
    """Write the YAML polygons into ``areas.boundary``; returns the number of areas updated.

    An area with ``name_vi`` and ``name_en`` in the YAML is created when missing and renamed
    when its names changed; an area without names must already exist (seeded).
    """
    polygons = load_areas(city_code) if areas is None else tuple(areas)
    city_id = await session.scalar(select(City.id).where(City.code == city_code))
    if city_id is None:
        raise ValueError(f"city {city_code} is not seeded")
    updated = 0
    next_sort = int(
        await session.scalar(
            select(func.coalesce(func.max(Area.sort_order), 0)).where(Area.city_id == city_id)
        )
        or 0
    )
    for polygon in polygons:
        if polygon.name_vi and polygon.name_en:
            exists = await session.scalar(
                select(Area.code).where(Area.code == polygon.code, Area.city_id == city_id)
            )
            if exists is None:
                next_sort += 1
                await session.execute(
                    insert(Area)
                    .values(
                        code=polygon.code,
                        city_id=city_id,
                        name_vi=polygon.name_vi,
                        name_en=polygon.name_en,
                        sort_order=next_sort,
                    )
                    .on_conflict_do_nothing()
                )
            else:
                await session.execute(
                    update(Area)
                    .where(Area.code == polygon.code, Area.city_id == city_id)
                    .values(name_vi=polygon.name_vi, name_en=polygon.name_en)
                )
        result = await session.execute(
            update(Area)
            .where(Area.code == polygon.code, Area.city_id == city_id)
            .values(boundary=polygon.ewkt())
        )
        updated += int(getattr(result, "rowcount", 0) or 0)
    return updated

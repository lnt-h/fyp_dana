"""Travel-area polygons and point-in-polygon assignment (pure Python, DEC-022).

``data/areas/<city>.yaml`` is the owner-maintained source. Assignment is first match in file
order; ``write_area_boundaries`` copies the polygons into ``areas.boundary`` for SQL users.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reference import Area, City

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
AREAS_DIR = DATA_DIR / "areas"

Ring = tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class AreaPolygon:
    code: str
    ring: Ring  # closed: first point == last point; (lng, lat)

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
        areas.append(AreaPolygon(code=code, ring=tuple(points)))
    return tuple(areas)


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
    """Write the YAML polygons into ``areas.boundary``; returns the number of areas updated."""
    polygons = load_areas(city_code) if areas is None else tuple(areas)
    city_id = await session.scalar(select(City.id).where(City.code == city_code))
    if city_id is None:
        raise ValueError(f"city {city_code} is not seeded")
    updated = 0
    for polygon in polygons:
        result = await session.execute(
            update(Area)
            .where(Area.code == polygon.code, Area.city_id == city_id)
            .values(boundary=polygon.ewkt())
        )
        updated += int(getattr(result, "rowcount", 0) or 0)
    return updated

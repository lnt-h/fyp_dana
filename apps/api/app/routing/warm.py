"""``routes warm``: pre-fill ``routes_matrix_cache`` for published places and anchors (ADR-012).

Exposed as a function only; the Typer command in ``app/cli.py`` wires it (see M3-B handoff).
For 50 places × 4 anchors this is ≈ 2 900 DRIVE elements plus the WALK pairs ≤ 2.5 km; already
cached pairs cost nothing, quota exhaustion stops spending (remaining legs stay uncached).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from app.routing.anchors import DA_NANG_ANCHORS, Anchor
from app.routing.matrix import MatrixStats, QuotaGate, get_matrix
from app.routing.matrix_cache import MatrixCache, SessionFactory
from app.routing.provider import LatLng, RoutesProvider, TravelMode

logger = logging.getLogger("gonarra.routing")

DEFAULT_WARM_PLACE_LIMIT = 50

_PUBLISHED_POINTS = text(
    "SELECT v.place_id, ST_Y(geometry(v.location)) AS lat, ST_X(geometry(v.location)) AS lng "
    "FROM vw_published_places v JOIN cities c ON c.id = v.city_id "
    "WHERE c.code = :city_code ORDER BY v.place_id LIMIT :limit"
)


@dataclass(frozen=True, slots=True)
class WarmReport:
    points: int
    by_mode: dict[str, MatrixStats]


async def load_published_points(
    session_factory: SessionFactory, *, city_code: str, limit: int
) -> dict[str, LatLng]:
    """``place:<uuid>`` → coordinates for published places of ``city_code`` (stable order)."""
    async with session_factory() as session:
        rows = (
            (await session.execute(_PUBLISHED_POINTS, {"city_code": city_code, "limit": limit}))
            .mappings()
            .all()
        )
    return {
        f"place:{row['place_id']}": LatLng(float(row["lat"]), float(row["lng"])) for row in rows
    }


async def warm_routes(
    session_factory: SessionFactory | None,
    *,
    ledger: QuotaGate,
    provider: RoutesProvider,
    city_code: str = "da-nang",
    place_limit: int = DEFAULT_WARM_PLACE_LIMIT,
    anchors: Sequence[Anchor] = DA_NANG_ANCHORS,
    modes: Sequence[TravelMode] = ("DRIVE", "WALK"),
    points: dict[str, LatLng] | None = None,
    cache: MatrixCache | None = None,
    clock: Callable[[], datetime] | None = None,
) -> WarmReport:
    """Fill the cache for every ordered pair among published places and fixed anchors.

    ``points`` overrides the catalog query (tests). Only a persistable (Google) provider makes
    warming meaningful; with any other provider nothing is written.
    """
    if not provider.persistable:
        logger.warning("routes warm provider=%s not persistable; nothing cached", provider.kind)
    if points is None:
        if session_factory is None:
            raise ValueError("session_factory is required to load published places")
        points = await load_published_points(
            session_factory, city_code=city_code, limit=place_limit
        )
    keyed: dict[str, LatLng] = {anchor.key: anchor.location for anchor in anchors}
    keyed.update(points)
    by_mode: dict[str, MatrixStats] = {}
    for mode in modes:
        matrix = await get_matrix(
            session_factory,
            keys_with_coords=keyed,
            mode=mode,
            ledger=ledger,
            provider=provider,
            cache=cache,
            clock=clock,
        )
        by_mode[mode] = matrix.stats
    return WarmReport(points=len(keyed), by_mode=by_mode)

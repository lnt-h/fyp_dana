"""Retention sweep of the provider caches (ADR-006): ``uv run python -m app.cli caches sweep``.

Deletes expired rows and clears expired Google Places coordinates. Every statement is
idempotent: a second run (or a run with nothing expired) changes nothing. Only row counts are
reported; no cached content is read or logged.

* ``research_cache`` — Tavily results and fetched page text, rows past ``expires_at`` (≤ 7 d).
* ``routes_matrix_cache`` — Google Routes legs past ``expires_at`` (≤ 30 d).
* ``places_lookup_cache`` — lat/lng cleared once ``location_expires_at`` passed or the row is
  older than 30 days (ADR-006 lat/lng ≤ 30 d); rows past ``outcome_expires_at`` (≤ 24 h) deleted.
* ``query_embedding_cache`` — rows past ``expires_at`` (90 d), when the table exists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Final

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

PLACES_LOCATION_MAX_AGE: Final = timedelta(days=30)

_DELETE_EXPIRED: Final = {
    "research_cache": text("DELETE FROM research_cache WHERE expires_at <= :now"),
    "routes_matrix_cache": text("DELETE FROM routes_matrix_cache WHERE expires_at <= :now"),
    "places_lookup_cache": text("DELETE FROM places_lookup_cache WHERE outcome_expires_at <= :now"),
    "query_embedding_cache": text("DELETE FROM query_embedding_cache WHERE expires_at <= :now"),
}
_CLEAR_PLACES_LOCATION: Final = text(
    "UPDATE places_lookup_cache SET location = NULL, location_expires_at = NULL "
    "WHERE location IS NOT NULL AND (location_expires_at <= :now OR fetched_at <= :cutoff)"
)
_TABLE_EXISTS: Final = text("SELECT to_regclass(:name) IS NOT NULL")


@dataclass
class SweepReport:
    deleted: dict[str, int] = field(default_factory=dict)
    places_locations_cleared: int = 0
    skipped: list[str] = field(default_factory=list)  # tables absent from this database


async def sweep_caches(session: AsyncSession, *, now: datetime) -> SweepReport:
    """Run the sweep in one transaction and commit it."""
    report = SweepReport()
    # Coordinates first: a row whose outcome also expired is deleted below anyway.
    if await session.scalar(_TABLE_EXISTS, {"name": "public.places_lookup_cache"}):
        cleared = await session.execute(
            _CLEAR_PLACES_LOCATION, {"now": now, "cutoff": now - PLACES_LOCATION_MAX_AGE}
        )
        report.places_locations_cleared = _rowcount(cleared)
    for table, statement in _DELETE_EXPIRED.items():
        if not await session.scalar(_TABLE_EXISTS, {"name": f"public.{table}"}):
            report.skipped.append(table)
            continue
        report.deleted[table] = _rowcount(await session.execute(statement, {"now": now}))
    await session.commit()
    return report


def _rowcount(result: object) -> int:
    count = getattr(result, "rowcount", 0)
    return count if isinstance(count, int) and count > 0 else 0

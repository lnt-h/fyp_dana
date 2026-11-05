"""Shared curation helpers: cursors, normalisation, geometry, audit, constraint errors."""

from __future__ import annotations

import base64
import binascii
import json
import re
import unicodedata
import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.types import ewkt_point
from app.errors import AppError, invalid, not_found
from app.models.catalog import CatalogAuditEvent, Place, SourceRevision
from app.models.reference import City
from app.schemas.admin import GeoPoint

DEFAULT_LIMIT = 20
MAX_LIMIT = 50

_POINT = re.compile(r"POINT\(\s*(-?[0-9.eE+-]+)\s+(-?[0-9.eE+-]+)\s*\)")


# ---- Cursors ----------------------------------------------------------------------------
# Opaque offset cursors: curator lists are small (hundreds to low thousands of rows), so an
# offset keeps sorting by computed columns (names) simple. Clients must treat it as opaque.


def encode_cursor(offset: int) -> str:
    raw = json.dumps({"o": offset}, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        offset = json.loads(base64.urlsafe_b64decode(padded.encode()))["o"]
    except (ValueError, KeyError, TypeError, binascii.Error) as exc:
        raise AppError(400, "invalid_cursor", "Cursor is not valid") from exc
    if not isinstance(offset, int) or offset < 0:
        raise AppError(400, "invalid_cursor", "Cursor is not valid")
    return offset


def page_slice[T](rows: Sequence[T], offset: int, limit: int) -> tuple[list[T], str | None]:
    """``rows`` was fetched with ``limit + 1``; returns the page and the next cursor."""
    items = list(rows[:limit])
    next_cursor = encode_cursor(offset + limit) if len(rows) > limit else None
    return items, next_cursor


def clamp_limit(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    return max(1, min(MAX_LIMIT, limit))


# ---- Text -------------------------------------------------------------------------------


def normalize_search_text(value: str) -> str:
    """Lower case, diacritics removed, đ→d, whitespace collapsed (place_aliases, FR-002)."""
    lowered = value.strip().lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", lowered)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", stripped)


def slugify(value: str) -> str:
    normalized = normalize_search_text(value)
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug[:100] or "place"


# ---- Geometry ---------------------------------------------------------------------------


def to_ewkt(point: GeoPoint) -> str:
    return ewkt_point(point.longitude, point.latitude)


def parse_point(ewkt: str | None) -> GeoPoint | None:
    if not ewkt:
        return None
    match = _POINT.search(ewkt)
    if match is None:
        return None
    return GeoPoint(longitude=float(match.group(1)), latitude=float(match.group(2)))


# ---- Lookups ----------------------------------------------------------------------------


async def default_city_id(session: AsyncSession, city_code: str) -> uuid.UUID:
    city_id = await session.scalar(select(City.id).where(City.code == city_code))
    if city_id is None:
        raise invalid("city_not_found", "Default city is not seeded", city_code=city_code)
    return city_id


async def require_city(session: AsyncSession, city_id: uuid.UUID) -> City:
    city = await session.get(City, city_id)
    if city is None:
        raise invalid("city_not_found", "Unknown city", city_id=str(city_id))
    return city


async def get_place(session: AsyncSession, place_id: uuid.UUID, *, lock: bool = False) -> Place:
    statement = select(Place).where(Place.id == place_id)
    if lock:
        statement = statement.with_for_update()
    place = await session.scalar(statement)
    if place is None:
        raise not_found("Place not found", code="not_found")
    return place


async def require_source_revisions(
    session: AsyncSession, source_revision_ids: Sequence[uuid.UUID]
) -> None:
    wanted = set(source_revision_ids)
    if not wanted:
        return
    found = set(
        (
            await session.scalars(select(SourceRevision.id).where(SourceRevision.id.in_(wanted)))
        ).all()
    )
    missing = sorted(str(value) for value in wanted - found)
    if missing:
        raise invalid("unknown_source_revision", "Unknown source revision", ids=missing)


async def bump_content_revision(session: AsyncSession, place_id: uuid.UUID) -> None:
    await session.execute(
        update(Place)
        .where(Place.id == place_id)
        .values(content_revision=Place.content_revision + 1)
    )


# ---- Audit ------------------------------------------------------------------------------


def audit(
    session: AsyncSession,
    *,
    actor_account_id: uuid.UUID,
    entity_table: str,
    entity_id: uuid.UUID,
    action: str,
    from_state: str | None = None,
    to_state: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """Append one ``catalog_audit_events`` row in the caller's transaction."""
    session.add(
        CatalogAuditEvent(
            actor_account_id=actor_account_id,
            entity_table=entity_table,
            entity_id=entity_id,
            action=action,
            from_state=from_state,
            to_state=to_state,
            detail=detail or {},
        )
    )


# ---- Transactions -----------------------------------------------------------------------


def constraint_error(exc: DBAPIError) -> AppError:
    """Map a database constraint failure to the error envelope (422 / 409)."""
    orig = exc.orig
    diag = getattr(orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None)
    sqlstate = getattr(orig, "sqlstate", None)
    if sqlstate == "23505":
        return AppError(
            409, "conflict", "Conflicts with an existing record", context={"constraint": constraint}
        )
    return AppError(
        422,
        "constraint_violation",
        "The change violates a catalog rule",
        context={"constraint": constraint, "sqlstate": sqlstate},
    )


async def commit(session: AsyncSession) -> None:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise constraint_error(exc) from exc


async def flush(session: AsyncSession) -> None:
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise constraint_error(exc) from exc

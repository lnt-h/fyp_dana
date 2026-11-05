"""Place search over published places (FR-002, FR-004, NFR-001; query Q-S1).

Matching is diacritic- and case-insensitive: the query is normalised with
:func:`normalize_search_text` and compared to ``place_aliases.alias_normalized`` (reviewed names
and aliases, VI and EN) using substring and pg_trgm similarity (GIN trigram index). Results are
paged with a stable keyset cursor.

Cursor format (opaque to clients): base64url without padding of compact JSON
``{"v": 1, "f": <filter fingerprint>, "k": [<sort key>, "<place_id>"]}`` where the sort key is the
relevance score (float, ``sort=relevance`` with ``q``) or the lower-cased name in the requested
locale (``sort=name``, or ``relevance`` without ``q``). ``f`` is the first 16 hex characters of the
SHA-256 of the normalised filters, so a cursor replayed with different filters is rejected.
"""

import base64
import binascii
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import Float, and_, case, func, literal, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.normalize import normalize_search_text
from app.catalog.places import (
    PlaceSummaryRecord,
    attach_thumbnails,
    published_places_select,
    vw_published_places,
)
from app.models.catalog import CatalogPublication, PlaceAlias

SortOrder = Literal["relevance", "name"]
CURSOR_VERSION = 1
MAX_LIMIT = 50


class InvalidCursorError(ValueError):
    """The cursor is malformed or was issued for different filters."""


@dataclass(frozen=True)
class BoundingBox:
    min_lng: float
    min_lat: float
    max_lng: float
    max_lat: float


@dataclass(frozen=True)
class Near:
    lat: float
    lng: float
    radius_m: float


@dataclass(frozen=True)
class SearchPage:
    items: list[PlaceSummaryRecord]
    next_cursor: str | None


def _fingerprint(filters: dict[str, Any]) -> str:
    payload = json.dumps(filters, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def encode_cursor(fingerprint: str, sort_key: float | str, place_id: uuid.UUID) -> str:
    payload = json.dumps(
        {"v": CURSOR_VERSION, "f": fingerprint, "k": [sort_key, str(place_id)]},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()


def decode_cursor(
    cursor: str, fingerprint: str, key_type: type[float] | type[str]
) -> tuple[float | str, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("v") != CURSOR_VERSION:
            raise InvalidCursorError("unsupported cursor version")
        if data.get("f") != fingerprint:
            raise InvalidCursorError("cursor does not match the request filters")
        key, place_id = data["k"]
        if key_type is float:
            if isinstance(key, bool) or not isinstance(key, int | float):
                raise InvalidCursorError("cursor sort key has the wrong type")
            return float(key), uuid.UUID(place_id)
        if not isinstance(key, str):
            raise InvalidCursorError("cursor sort key has the wrong type")
        return key, uuid.UUID(place_id)
    except InvalidCursorError:
        raise
    except (binascii.Error, ValueError, KeyError, TypeError, UnicodeDecodeError) as exc:
        raise InvalidCursorError("malformed cursor") from exc


async def search_catalog(
    session: AsyncSession,
    *,
    city_id: uuid.UUID,
    q: str | None = None,
    category_code: str | None = None,
    area_code: str | None = None,
    bbox: BoundingBox | None = None,
    near: Near | None = None,
    sort: SortOrder = "relevance",
    locale: str = "vi",
    cursor: str | None = None,
    limit: int = 20,
) -> SearchPage:
    """One page of published places of ``city_id`` matching the filters.

    ``q`` is matched against approved aliases of both locales after normalisation; an empty
    normalised query behaves like no query. Category codes are compared in UPPER_CASE.
    Raises :class:`InvalidCursorError` for a malformed or foreign cursor.
    """
    vw = vw_published_places
    limit = max(1, min(limit, MAX_LIMIT))
    normalized_q = normalize_search_text(q) if q else ""
    category = category_code.strip().upper() if category_code else None
    use_score = bool(normalized_q) and sort == "relevance"
    fingerprint = _fingerprint(
        {
            "city_id": str(city_id),
            "q": normalized_q,
            "category": category,
            "area": area_code,
            "bbox": bbox,
            "near": near,
            "sort": "relevance" if use_score else "name",
            "locale": locale,
        }
    )

    stmt = published_places_select().where(vw.c.city_id == city_id)
    if category:
        stmt = stmt.where(vw.c.category_code == category)
    if area_code:
        stmt = stmt.where(CatalogPublication.area_code == area_code)
    if bbox is not None:
        stmt = stmt.where(
            func.ST_Intersects(
                func.geometry(vw.c.location),
                func.ST_MakeEnvelope(bbox.min_lng, bbox.min_lat, bbox.max_lng, bbox.max_lat, 4326),
            )
        )
    if near is not None:
        stmt = stmt.where(
            func.ST_DWithin(
                vw.c.location,
                func.geography(func.ST_SetSRID(func.ST_MakePoint(near.lng, near.lat), 4326)),
                near.radius_m,
            )
        )

    score = None
    if normalized_q:
        alias = PlaceAlias.alias_normalized
        q_param = literal(normalized_q)
        alias_score = (
            case(
                (alias == q_param, 3.0),
                (alias.startswith(normalized_q, autoescape=True), 2.0),
                (alias.contains(normalized_q, autoescape=True), 1.0),
                else_=0.0,
            )
            + func.greatest(func.similarity(alias, q_param), func.word_similarity(q_param, alias))
        ).cast(Float)
        matches = (
            select(PlaceAlias.place_id, func.max(alias_score).label("score"))
            .where(
                PlaceAlias.review_state == "APPROVED",
                or_(
                    alias.contains(normalized_q, autoescape=True),
                    alias.op("%")(q_param),
                    q_param.op("<%")(alias),
                ),
            )
            .group_by(PlaceAlias.place_id)
            .subquery("alias_matches")
        )
        stmt = stmt.join(matches, matches.c.place_id == vw.c.place_id)
        score = matches.c.score
        stmt = stmt.add_columns(score.label("score"))

    name_key = func.lower(vw.c.name_en if locale == "en" else vw.c.name_vi)
    stmt = stmt.add_columns(name_key.label("name_key"))

    if use_score:
        assert score is not None
        if cursor:
            after_score, after_id = decode_cursor(cursor, fingerprint, float)
            stmt = stmt.where(
                or_(score < after_score, and_(score == after_score, vw.c.place_id > after_id))
            )
        stmt = stmt.order_by(score.desc(), vw.c.place_id)
    else:
        if cursor:
            after_name, after_id = decode_cursor(cursor, fingerprint, str)
            stmt = stmt.where(tuple_(name_key, vw.c.place_id) > tuple_(after_name, after_id))
        stmt = stmt.order_by(name_key, vw.c.place_id)

    rows = (await session.execute(stmt.limit(limit + 1))).all()
    page_rows = rows[:limit]
    next_cursor = None
    if len(rows) > limit:
        last = page_rows[-1]
        next_cursor = encode_cursor(
            fingerprint, float(last.score) if use_score else last.name_key, last.place_id
        )
    return SearchPage(items=await attach_thumbnails(session, page_rows), next_cursor=next_cursor)

"""Catalog routes (openapi.yaml API-008..API-011): cities, categories, place search and detail.

All routes require a verified session (contract ``security: HTTPBearer``). Only published places
of an enabled city are ever returned (FR-001, FR-004); they always carry ``trust_level=VERIFIED``.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalog.places import (
    FactRecord,
    MediaRecord,
    PlaceDetailRecord,
    PlacesRepository,
    PlaceSummaryRecord,
)
from app.catalog.preferences import DEFAULT_LOCALE, PreferencesRepository
from app.catalog.reference import AreaRecord, CityRecord, ReferenceRepository
from app.catalog.search import BoundingBox, InvalidCursorError, Near, search_catalog
from app.config import get_settings
from app.db.session import get_db_session
from app.errors import AppError
from app.models.account import Account
from app.schemas.catalog import (
    Area,
    Attribution,
    Category,
    CategoryList,
    Citation,
    City,
    CityList,
    ClosureRule,
    GeoPoint,
    Locale,
    Media,
    PlaceDetail,
    PlaceFact,
    PlaceSummary,
    PlaceSummaryPage,
    SearchSort,
)
from app.schemas.common import ErrorResponse
from app.security.clerk import get_optional_account

router = APIRouter(tags=["catalog"])

Session = Annotated[AsyncSession, Depends(get_db_session)]
# Public catalog reads (2026-11-08): guests are anonymous; a sent token must be valid.
OptionalAccount = Annotated[Account | None, Depends(get_optional_account)]

# Optional bearer auth in the generated contract (openapi 1.0.3 `security: [{}, HTTPBearer]`).
PUBLIC: dict[str, Any] = {"security": [{}, {"HTTPBearer": []}]}

# 401 only for an invalid token; a request without a token is served anonymously.
AUTH_RESPONSES: dict[int | str, dict[str, object]] = {
    401: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


async def resolve_locale(
    account: OptionalAccount,
    session: Session,
    locale: Annotated[
        Locale | None,
        Query(description="Content language; defaults to the account preference, then vi."),
    ] = None,
) -> str:
    if locale is not None:
        return locale
    if account is None:
        return DEFAULT_LOCALE
    return await PreferencesRepository(session).get_locale(account.id) or DEFAULT_LOCALE


ResolvedLocale = Annotated[str, Depends(resolve_locale)]


def _invalid(field: str, message: str) -> AppError:
    return AppError(
        422,
        "validation_error",
        message,
        context={
            "fields": [{"type": "value_error", "location": ["query", field], "message": message}]
        },
    )


def _area(area: AreaRecord) -> Area:
    return Area(
        code=area.code, name_vi=area.name_vi, name_en=area.name_en, sort_order=area.sort_order
    )


def _city(city: CityRecord) -> City:
    centre = (
        GeoPoint(latitude=city.centre_lat, longitude=city.centre_lng)
        if city.centre_lat is not None and city.centre_lng is not None
        else None
    )
    return City(
        id=city.id,
        code=city.code,
        name_vi=city.name_vi,
        name_en=city.name_en,
        time_zone=city.time_zone,
        centre=centre,
        areas=[_area(area) for area in city.areas],
    )


def _media(media: MediaRecord, locale: str) -> Media:
    base = get_settings().media_base_url.rstrip("/")
    # Hot-linked Wikimedia Commons files store their absolute https URL as the object key.
    key = media.object_key
    url = key if key.startswith("https://") else f"{base}/{key.lstrip('/')}"
    return Media(
        media_asset_id=media.media_asset_id,
        url=url,
        width_px=media.width_px,
        height_px=media.height_px,
        alt_text=media.alt_text_en if locale == "en" else media.alt_text_vi,
        creator=media.creator,
        license_code=media.license_code,
        attribution_text=media.attribution_text,
    )


def _summary(place: PlaceSummaryRecord, locale: str) -> PlaceSummary:
    return PlaceSummary(
        id=place.place_id,
        city_id=place.city_id,
        slug=place.slug,
        category_code=place.category_code,
        area_code=place.area_code,
        name_vi=place.name_vi,
        name=place.name(locale),
        name_is_source_fallback=place.name_is_source_fallback(locale),
        short_description=place.short_description(locale),
        location=GeoPoint(latitude=place.lat, longitude=place.lng),
        visit_minutes_suggested=place.visit_minutes_suggested,
        catalog_publication_id=place.catalog_publication_id,
        thumbnail=_media(place.thumbnail, locale) if place.thumbnail else None,
        trust_level=place.trust_level,
    )


def _fact(fact: FactRecord) -> PlaceFact:
    verified_on = fact.verified_at.date() if fact.verified_at else None
    citations = [
        Citation(
            source_revision_id=source.source_revision_id,
            place_fact_id=fact.place_fact_id,
            publisher=source.publisher,
            title=source.title,
            locator=source.locator,
            verified_at=verified_on or source.retrieved_at.date(),
        )
        for source in fact.sources
    ]
    return PlaceFact(
        place_fact_id=fact.place_fact_id,
        field_code=fact.field_code,
        knowledge_state=fact.knowledge_state,
        # Unknown stays unknown (FR-005): a value is shown only for KNOWN facts.
        value=fact.value if fact.knowledge_state == "KNOWN" else None,
        verified_at=verified_on,
        valid_until=fact.valid_until,
        freshness="STALE" if fact.is_stale else "CURRENT",
        source=citations[0] if citations else None,
        sources=citations,
    )


def _attributions(detail: PlaceDetailRecord) -> list[Attribution]:
    seen: set[tuple[str, str]] = set()
    result: list[Attribution] = []
    for fact in detail.facts:
        for source in fact.sources:
            if source.attribution_text is None:
                continue
            key = (source.publisher, source.attribution_text)
            if key not in seen:
                seen.add(key)
                result.append(
                    Attribution(
                        publisher=source.publisher,
                        attribution_text=source.attribution_text,
                        license_code=source.license_code,
                        homepage_url=source.homepage_url,
                    )
                )
    for media in detail.media:
        key = (media.creator, media.attribution_text)
        if key not in seen:
            seen.add(key)
            result.append(
                Attribution(
                    publisher=media.creator,
                    attribution_text=media.attribution_text,
                    license_code=media.license_code,
                )
            )
    return result


def _detail(detail: PlaceDetailRecord, locale: str) -> PlaceDetail:
    entrance = (
        GeoPoint(latitude=detail.entrance_lat, longitude=detail.entrance_lng)
        if detail.entrance_lat is not None and detail.entrance_lng is not None
        else None
    )
    description = detail.description_en if locale == "en" else detail.description_vi
    origin = detail.translation_origin_en if locale == "en" else detail.translation_origin_vi
    return PlaceDetail(
        **_summary(detail.summary, locale).model_dump(),
        name_en=detail.summary.name_en,
        description=description,
        description_origin=(
            None if not description else "AI_SUMMARY" if origin == "AI_SUMMARY" else "SOURCE"
        ),
        visit_minutes_min=detail.visit_minutes_min,
        visit_minutes_max=detail.visit_minutes_max,
        entrance_location=entrance,
        area=_area(detail.area) if detail.area else None,
        publication_revision=detail.publication_revision,
        published_at=detail.published_at,
        facts=[_fact(fact) for fact in detail.facts],
        media=[_media(media, locale) for media in detail.media],
        closure_rules=[
            ClosureRule(
                id=rule.id,
                applies_to=rule.applies_to,
                rule_kind=rule.rule_kind,
                effect=rule.effect,
                severity=rule.severity,
                params=rule.params,
                note=rule.note_en if locale == "en" else rule.note_vi,
                effective_from=rule.effective_from,
                effective_to=rule.effective_to,
                verified_at=rule.verified_at.date() if rule.verified_at else None,
            )
            for rule in detail.closure_rules
        ],
        attributions=_attributions(detail),
    )


def _parse_floats(raw: str, count: int, field: str) -> list[float]:
    try:
        values = [float(part) for part in raw.split(",")]
    except ValueError:
        values = []
    if len(values) != count:
        raise _invalid(field, f"{field} needs {count} comma-separated numbers")
    return values


def _bbox(raw: str | None) -> BoundingBox | None:
    if raw is None:
        return None
    min_lng, min_lat, max_lng, max_lat = _parse_floats(raw, 4, "bbox")
    if not (-180 <= min_lng < max_lng <= 180 and -90 <= min_lat < max_lat <= 90):
        raise _invalid("bbox", "bbox must be min_lng,min_lat,max_lng,max_lat with min < max")
    return BoundingBox(min_lng, min_lat, max_lng, max_lat)


def _near(raw: str | None, radius_m: int) -> Near | None:
    if raw is None:
        return None
    lat, lng = _parse_floats(raw, 2, "near")
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise _invalid("near", "near must be lat,lng within range")
    return Near(lat=lat, lng=lng, radius_m=float(radius_m))


@router.get("/cities", response_model=CityList, responses=AUTH_RESPONSES, openapi_extra=PUBLIC)
async def list_cities(account: OptionalAccount, session: Session) -> CityList:
    """Enabled cities with their travel areas (FR-001; one city, Đà Nẵng, for the FYP)."""
    cities = await ReferenceRepository(session).list_enabled_cities()
    return CityList(items=[_city(city) for city in cities])


@router.get(
    "/categories", response_model=CategoryList, responses=AUTH_RESPONSES, openapi_extra=PUBLIC
)
async def list_categories(account: OptionalAccount, session: Session) -> CategoryList:
    categories = await ReferenceRepository(session).list_categories()
    return CategoryList(
        items=[
            Category(code=c.code, name_vi=c.name_vi, name_en=c.name_en, sort_order=c.sort_order)
            for c in categories
        ]
    )


@router.get(
    "/places",
    response_model=PlaceSummaryPage,
    responses={**AUTH_RESPONSES, 400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
    openapi_extra=PUBLIC,
)
async def search_places(
    session: Session,
    locale: ResolvedLocale,
    city_id: Annotated[
        uuid.UUID | None,
        Query(description="Enabled city; defaults to the enabled launch city (Đà Nẵng)."),
    ] = None,
    city_code: Annotated[
        str | None, Query(max_length=64, description="Alternative to city_id, e.g. da-nang.")
    ] = None,
    q: Annotated[
        str | None,
        Query(min_length=1, max_length=120, description="Search text; omitted lists places."),
    ] = None,
    category_code: Annotated[
        str | None,
        Query(max_length=64, description="Category code; case-insensitive (HERITAGE, heritage)."),
    ] = None,
    area_code: Annotated[
        str | None, Query(max_length=64, description="Travel area, e.g. hoi-an-old-town.")
    ] = None,
    bbox: Annotated[
        str | None,
        Query(max_length=128, description="min_lng,min_lat,max_lng,max_lat (WGS84)."),
    ] = None,
    near: Annotated[
        str | None, Query(max_length=64, description="lat,lng; combine with radius_m.")
    ] = None,
    radius_m: Annotated[int, Query(ge=1, le=50_000)] = 1_000,
    sort: Annotated[SearchSort, Query()] = "relevance",
    cursor: Annotated[
        str | None,
        Query(max_length=512, description="Opaque cursor from a previous page's next_cursor."),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> PlaceSummaryPage:
    """Search published places by VI/EN name or reviewed alias, ignoring case and diacritics."""
    reference = ReferenceRepository(session)
    if city_id is None and city_code is None:
        city_code = get_settings().default_city_code
    city = await reference.get_enabled_city(city_id=city_id, city_code=city_code)
    if city is None:
        raise _invalid("city_id" if city_id else "city_code", "city is not an enabled city")
    if area_code is not None and area_code not in {area.code for area in city.areas}:
        raise _invalid("area_code", "area_code is not a travel area of this city")
    try:
        page = await search_catalog(
            session,
            city_id=city.id,
            q=q,
            category_code=category_code,
            area_code=area_code,
            bbox=_bbox(bbox),
            near=_near(near, radius_m),
            sort=sort,
            locale=locale,
            cursor=cursor,
            limit=limit,
        )
    except InvalidCursorError as exc:
        raise AppError(status.HTTP_400_BAD_REQUEST, "invalid_cursor", str(exc)) from exc
    return PlaceSummaryPage(
        items=[_summary(item, locale) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.get(
    "/places/{place_id}",
    response_model=PlaceDetail,
    responses={**AUTH_RESPONSES, 404: {"model": ErrorResponse}},
    openapi_extra=PUBLIC,
)
async def get_place(place_id: uuid.UUID, session: Session, locale: ResolvedLocale) -> PlaceDetail:
    """Current publication of a place with facts, freshness, attribution and closure rules."""
    detail = await PlacesRepository(session).get_published_detail(place_id)
    enabled = {city.id for city in await ReferenceRepository(session).list_enabled_cities()}
    if detail is None or detail.summary.city_id not in enabled:
        # Candidates and unknown IDs are indistinguishable (FR-004).
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return _detail(detail, locale)

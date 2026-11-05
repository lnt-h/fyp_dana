"""Trips, place card, booking handoff and stay prices (API-012..017, API-030, API-031)."""

import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.errors import AppError
from app.models.account import Account
from app.schemas.common import ErrorResponse
from app.schemas.trips import (
    HandoffKind,
    HandoffLink,
    Locale,
    PartnerKey,
    PlaceCard,
    Trip,
    TripCreate,
    TripDetail,
    TripPage,
    TripStatus,
    TripUpdate,
)
from app.security.clerk import get_current_account
from app.trips import idempotency
from app.trips.repository import SQLAlchemyTripStore, TripStore
from app.trips.service import TripService

router = APIRouter(tags=["trips"])


def get_trip_store(session: Annotated[AsyncSession, Depends(get_db_session)]) -> TripStore:
    return SQLAlchemyTripStore(session)


def get_trip_service(
    account: Annotated[Account, Depends(get_current_account)],
    store: Annotated[TripStore, Depends(get_trip_store)],
) -> TripService:
    return TripService(store, account.id)


Service = Annotated[TripService, Depends(get_trip_service)]
LocaleQuery = Annotated[Locale | None, Query()]


def errors(*codes: int) -> dict[int | str, dict[str, Any]]:
    return {code: {"model": ErrorResponse} for code in (401, 503, *codes)}


@router.get("/trips", response_model=TripPage, responses=errors(400))
async def list_trips(
    service: Service,
    status_filter: Annotated[TripStatus | None, Query(alias="status")] = None,
    sort: Annotated[Literal["-updated_at", "start_date"], Query()] = "-updated_at",
    cursor: Annotated[str | None, Query(max_length=512)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> TripPage:
    return await service.list_trips(status=status_filter, sort=sort, cursor=cursor, limit=limit)


@router.post(
    "/trips",
    response_model=Trip,
    status_code=status.HTTP_201_CREATED,
    responses=errors(409, 422),
)
async def create_trip(
    body: TripCreate,
    response: Response,
    service: Service,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> Trip:
    # Validated per the contract; not persisted: idempotency_records has no TRIP_CREATE operation.
    idempotency.normalize_key(idempotency_key, required=False)
    trip = await service.create_trip(body)
    response.headers["Location"] = f"/v1/trips/{trip.id}"
    return trip


@router.get("/trips/{trip_id}", response_model=TripDetail, responses=errors(404))
async def get_trip(trip_id: uuid.UUID, service: Service, locale: LocaleQuery = None) -> TripDetail:
    return await service.get_trip(trip_id, locale)


@router.patch("/trips/{trip_id}", response_model=Trip, responses=errors(404, 409, 422))
async def update_trip(trip_id: uuid.UUID, body: TripUpdate, service: Service) -> Trip:
    return await service.update_trip(trip_id, body)


@router.delete(
    "/trips/{trip_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=errors(404, 409),
)
async def delete_trip(
    trip_id: uuid.UUID,
    service: Service,
    expected_revision: Annotated[int, Query(ge=0)],
) -> Response:
    await service.delete_trip(trip_id, expected_revision)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/trips/{trip_id}/stops/{stop_id}/place-card",
    response_model=PlaceCard,
    responses=errors(404),
)
async def get_place_card(
    trip_id: uuid.UUID, stop_id: uuid.UUID, service: Service, locale: LocaleQuery = None
) -> PlaceCard:
    return await service.place_card(trip_id, stop_id, locale)


@router.get(
    "/trips/{trip_id}/handoff-links",
    response_model=HandoffLink,
    tags=["stays"],
    responses=errors(404, 409, 422),
)
async def get_handoff_link(
    trip_id: uuid.UUID,
    service: Service,
    kind: Annotated[HandoffKind, Query()],
    stop_id: Annotated[uuid.UUID | None, Query()] = None,
    partner: Annotated[
        PartnerKey | None,
        Query(description="Extension: STAY partner choice (agoda default, booking_com)."),
    ] = None,
    locale: LocaleQuery = None,
) -> HandoffLink:
    return await service.handoff_link(
        trip_id, kind=kind, stop_id=stop_id, partner=partner, locale=locale
    )


@router.get(
    "/trips/{trip_id}/stay-prices",
    tags=["stays"],
    responses=errors(404, 501),
)
async def get_stay_prices(
    trip_id: uuid.UUID,
    service: Service,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    """Could-scope (DEC-019): behind ``GONARRA_STAY_PRICES_ENABLED``; never stored."""
    if not settings.stay_prices_enabled:
        raise AppError(404, "feature_disabled", "Indicative stay prices are not enabled")
    await service.owned_trip(trip_id)
    raise AppError(
        501,
        "not_implemented",
        "Indicative stay prices are not available yet",
        headers={"Cache-Control": "no-store"},
    )

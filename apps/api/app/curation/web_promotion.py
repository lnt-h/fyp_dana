"""Automatic promotion of research-agent web candidates (DEC-022 replaces the curator queue).

A PENDING candidate becomes a DRAFT (IMPORTED) place only when the Google Places existence
check said ``EXISTS_OPERATIONAL`` and its stored location lies inside the city boundary. The
promoted place then goes through the same automated publication gate as every import (it
usually still lacks descriptions and stays unpublished). Anything else stays WEB_UNVERIFIED.
Google data is identifier-only: the place keeps ``google_place_id`` as an external identity,
never Google coordinates (ADR-006).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.common import audit, parse_point
from app.curation.system import system_account_id
from app.ingestion.areas import assign_area, load_areas
from app.ingestion.common import (
    create_place,
    free_slug,
    inside_city,
    link_identity,
    provider_id_for,
)
from app.models.catalog import WebPlaceCandidate
from app.models.reference import Category, City

GOOGLE_PLACES_PROVIDER_KEY = "google_places"


@dataclass(frozen=True)
class PromotionResult:
    candidate_id: uuid.UUID
    promoted: bool
    reason: str
    place_id: uuid.UUID | None = None


async def promote_web_candidate_if_eligible(
    session: AsyncSession, candidate_id: uuid.UUID
) -> PromotionResult:
    """Promote one candidate when eligible; never commits (the caller owns the transaction)."""
    candidate = await session.scalar(
        select(WebPlaceCandidate).where(WebPlaceCandidate.id == candidate_id).with_for_update()
    )
    if candidate is None:
        return PromotionResult(candidate_id, False, "NOT_FOUND")
    if candidate.review_state != "PENDING":
        return PromotionResult(candidate_id, False, f"STATE_{candidate.review_state}")
    if candidate.places_check_outcome != "EXISTS_OPERATIONAL":
        return PromotionResult(candidate_id, False, f"PLACES_{candidate.places_check_outcome}")
    point = parse_point(candidate.location) if candidate.location else None
    if point is None:
        return PromotionResult(candidate_id, False, "NO_LOCATION")
    if not await inside_city(session, candidate.city_id, point.longitude, point.latitude):
        return PromotionResult(candidate_id, False, "OUTSIDE_CITY")

    city_code = await session.scalar(select(City.code).where(City.id == candidate.city_id))
    assert city_code is not None
    category: str | None = None
    if candidate.category_guess:
        guess = candidate.category_guess.strip().upper()
        if await session.get(Category, guess) is not None:
            category = guess
    place = await create_place(
        session,
        city_id=candidate.city_id,
        slug=await free_slug(session, candidate.city_id, candidate.name_en or candidate.name),
        lng=point.longitude,
        lat=point.latitude,
        category_code=category,
        area_code=assign_area(load_areas(city_code), point.longitude, point.latitude),
    )
    google_provider = await provider_id_for(session, GOOGLE_PLACES_PROVIDER_KEY)
    if candidate.google_place_id and google_provider is not None:
        await link_identity(
            session,
            place_id=place.id,
            provider_id=google_provider,
            upstream_id=candidate.google_place_id,
            release=None,
        )
    actor = await system_account_id(session)
    now = datetime.now(UTC)
    candidate.review_state = "PROMOTED"
    candidate.promoted_place_id = place.id
    candidate.reviewed_by_account_id = actor
    candidate.reviewed_at = now
    candidate.review_note = "auto-promoted: EXISTS_OPERATIONAL inside the city boundary"
    await session.flush()
    audit(
        session,
        actor_account_id=actor,
        entity_table="web_place_candidates",
        entity_id=candidate.id,
        action="WEB_PROMOTE",
        from_state="PENDING",
        to_state="PROMOTED",
        detail={"place_id": str(place.id), "automated": True},
    )
    return PromotionResult(candidate_id, True, "PROMOTED", place.id)


async def promote_pending(session: AsyncSession, city_id: uuid.UUID) -> list[PromotionResult]:
    """Sweep every PENDING candidate of a city; commits once."""
    ids = (
        await session.scalars(
            select(WebPlaceCandidate.id)
            .where(
                WebPlaceCandidate.city_id == city_id,
                WebPlaceCandidate.review_state == "PENDING",
            )
            .order_by(WebPlaceCandidate.created_at)
        )
    ).all()
    results = [await promote_web_candidate_if_eligible(session, cid) for cid in ids]
    await session.commit()
    return results

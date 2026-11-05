"""Curator queue of research-agent candidates (ADR-014, ADR-012 0.4, API-046..049).

Every candidate is ``WEB_UNVERIFIED``. APPROVE promotes it into a place *draft*: a ``places``
row in IMPORTED, an approved ``external_place_identities`` row for the Google ``place_id``
(identifier only, ADR-006) and AI_DRAFT localization drafts. Nothing is published; the
ordinary review and publication gate still apply. REJECT records the curator's note.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation.candidates import apply_localizations
from app.curation.common import (
    audit,
    clamp_limit,
    commit,
    decode_cursor,
    flush,
    page_slice,
    parse_point,
    slugify,
    to_ewkt,
)
from app.errors import conflict, invalid, not_found
from app.models.catalog import Place, Source, SourceRevision, WebPlaceCandidate
from app.models.providers import DataProvider, ExternalPlaceIdentity
from app.models.reference import Category
from app.schemas.admin import (
    LocalizationInput,
    WebCandidate,
    WebCandidatePage,
    WebCandidateReview,
)

GOOGLE_PLACES_PROVIDER_KEY = "google_places"


class WebCandidateService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_candidates(
        self,
        *,
        review_state: str | None = "PENDING",
        city_id: uuid.UUID | None = None,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> WebCandidatePage:
        offset = decode_cursor(cursor)
        size = clamp_limit(limit)
        statement = self._base()
        if review_state is not None:
            statement = statement.where(WebPlaceCandidate.review_state == review_state)
        if city_id is not None:
            statement = statement.where(WebPlaceCandidate.city_id == city_id)
        statement = statement.order_by(WebPlaceCandidate.created_at.desc(), WebPlaceCandidate.id)
        rows = (await self._session.execute(statement.offset(offset).limit(size + 1))).all()
        page, next_cursor = page_slice(rows, offset, size)
        return WebCandidatePage(
            next_cursor=next_cursor, items=[_to_schema(row[0], row[1], row[2]) for row in page]
        )

    async def get_candidate(self, candidate_id: uuid.UUID) -> WebCandidate:
        row = (
            await self._session.execute(self._base().where(WebPlaceCandidate.id == candidate_id))
        ).first()
        if row is None:
            raise not_found("Web candidate not found")
        return _to_schema(row[0], row[1], row[2])

    async def review(
        self, candidate_id: uuid.UUID, data: WebCandidateReview, actor_account_id: uuid.UUID
    ) -> WebCandidate:
        candidate = await self._session.scalar(
            select(WebPlaceCandidate).where(WebPlaceCandidate.id == candidate_id).with_for_update()
        )
        if candidate is None:
            raise not_found("Web candidate not found")
        if candidate.review_state != "PENDING":
            raise conflict(
                "candidate_already_reviewed",
                "Only PENDING candidates can be reviewed",
                review_state=candidate.review_state,
            )
        now = datetime.now(UTC)
        if data.decision == "REJECT":
            candidate.review_state = "REJECTED"
            candidate.review_note = data.review_note
            action = "WEB_REJECT"
            detail: dict[str, object] = {"review_note_present": True}
        else:
            place = await self._promote(candidate, data)
            candidate.review_state = "PROMOTED"
            candidate.promoted_place_id = place.id
            candidate.review_note = data.review_note
            action = "WEB_PROMOTE"
            detail = {"place_id": str(place.id), "slug": place.slug}
        candidate.reviewed_at = now
        candidate.reviewed_by_account_id = actor_account_id
        await flush(self._session)
        audit(
            self._session,
            actor_account_id=actor_account_id,
            entity_table="web_place_candidates",
            entity_id=candidate.id,
            action=action,
            from_state="PENDING",
            to_state=candidate.review_state,
            detail=detail,
        )
        await commit(self._session)
        return await self.get_candidate(candidate_id)

    # ---- internals ----------------------------------------------------------------------

    def _base(self) -> Select[WebPlaceCandidate, str, str]:
        return (
            select(WebPlaceCandidate, SourceRevision.locator, Source.publisher)
            .join(SourceRevision, SourceRevision.id == WebPlaceCandidate.source_revision_id)
            .join(Source, Source.id == SourceRevision.source_id)
            .execution_options(populate_existing=True)
        )

    async def _promote(self, candidate: WebPlaceCandidate, data: WebCandidateReview) -> Place:
        if data.location is not None:
            location = to_ewkt(data.location)
        elif candidate.location is not None:
            location = candidate.location
        else:
            raise invalid(
                "location_required", "The candidate has no location; supply one to approve"
            )
        category_code = data.category_code
        if category_code is None and candidate.category_guess:
            guess = candidate.category_guess.strip().upper()
            if await self._session.get(Category, guess) is not None:
                category_code = guess
        slug = await self._free_slug(candidate.city_id, data.slug or slugify(candidate.name))
        place = Place(
            city_id=candidate.city_id,
            slug=slug,
            area_code=data.area_code,
            category_code=category_code,
            workflow_state="IMPORTED",
            location=location,
        )
        self._session.add(place)
        await flush(self._session)
        if candidate.google_place_id:
            provider_id = await self._session.scalar(
                select(DataProvider.id).where(
                    DataProvider.provider_key == GOOGLE_PLACES_PROVIDER_KEY
                )
            )
            if provider_id is not None:
                self._session.add(
                    ExternalPlaceIdentity(
                        place_id=place.id,
                        data_provider_id=provider_id,
                        upstream_id=candidate.google_place_id,
                        match_method="MANUAL",
                        review_state="APPROVED",
                        reviewed_at=datetime.now(UTC),
                    )
                )
        names = {
            "vi": data.name_vi or candidate.name_vi or candidate.name,
            "en": data.name_en or candidate.name_en or candidate.name,
        }
        await apply_localizations(
            self._session,
            place.id,
            [
                LocalizationInput(locale=locale, name=name, translation_origin="AI_DRAFT")
                for locale, name in names.items()
            ],
            [],
        )
        await flush(self._session)
        return place

    async def _free_slug(self, city_id: uuid.UUID, base: str) -> str:
        candidate = base
        suffix = 2
        while await self._session.scalar(
            select(Place.id).where(Place.city_id == city_id, Place.slug == candidate)
        ):
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate


def _to_schema(row: WebPlaceCandidate, locator: str | None, publisher: str | None) -> WebCandidate:
    return WebCandidate(
        id=row.id,
        city_id=row.city_id,
        name=row.name,
        name_vi=row.name_vi,
        name_en=row.name_en,
        category_guess=row.category_guess,
        location=parse_point(row.location),
        coordinate_source=row.coordinate_source,
        google_place_id=row.google_place_id,
        places_check_outcome=row.places_check_outcome,
        places_checked_at=row.places_checked_at,
        source_revision_id=row.source_revision_id,
        source_locator=locator,
        source_publisher=publisher,
        fetched_at=row.fetched_at,
        extraction=row.extraction,
        extraction_model=row.extraction_model,
        review_state=row.review_state,
        promoted_place_id=row.promoted_place_id,
        reviewed_by_account_id=row.reviewed_by_account_id,
        reviewed_at=row.reviewed_at,
        review_note=row.review_note,
        times_proposed=row.times_proposed,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

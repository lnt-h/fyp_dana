"""Trips, previews, Save, place card, handoff and deletion requests (ADR-009, CMP-007/008).

Every public method starts by loading the owned resource by ``(id, account_id)``; a foreign or
missing resource is 404 ``resource_not_found`` before any other check, model or provider call.
"""

import base64
import binascii
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any, Final
from urllib.parse import quote

from pydantic import ValidationError

from app.errors import AppError, not_found, revision_conflict, validation_failed
from app.models.planning import AccountDeletionJob, PlanPreview, PreviewRevision, Trip
from app.schemas.trips import (
    AcceptPreviewRequest,
    AccountDeletionStatus,
    Attribution,
    Citation,
    Directions,
    HandoffKind,
    HandoffLink,
    Locale,
    PartnerKey,
    PlaceCard,
    PlaceFact,
    PlanningPreferences,
    PlanPreviewEdit,
    TravelMode,
    TripCreate,
    TripDetail,
    TripPage,
    TripUpdate,
    WebSource,
)
from app.schemas.trips import (
    PlanPreview as PlanPreviewSchema,
)
from app.schemas.trips import Trip as TripSchema
from app.trips import idempotency
from app.trips.assumptions import localize_assumptions
from app.trips.handoff import HandoffTrip, build_handoff_link
from app.trips.render import DEFAULT_TIME_ZONE, candidate_names, parse_point, render_days
from app.trips.repository import CityInfo, FactInfo, TripCursor, TripSort, TripStore
from app.trips.snapshot import PlanSnapshot, apply_edits, evaluate_health

ADDRESS_FIELD: Final = "ADDRESS_VI"
ENTRANCE_FIELD: Final = "ENTRANCE_LOCATION"


@dataclass(frozen=True)
class IdempotentResult:
    """A JSON response body plus whether it was replayed from ``idempotency_records``."""

    body: dict[str, Any]
    replayed: bool
    status: int = 200


AcceptResult = IdempotentResult


def encode_cursor(sort: TripSort, trip: Trip) -> str:
    payload = {
        "s": sort,
        "u": trip.updated_at.isoformat() if trip.updated_at else None,
        "d": trip.start_date.isoformat() if trip.start_date else None,
        "i": str(trip.id),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str, sort: TripSort) -> TripCursor:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if payload["s"] != sort:
            raise ValueError("sort mismatch")
        return TripCursor(
            sort=sort,
            updated_at=datetime.fromisoformat(payload["u"]) if payload["u"] else None,
            start_date=date.fromisoformat(payload["d"]) if payload["d"] else None,
            trip_id=uuid.UUID(payload["i"]),
        )
    except (ValueError, KeyError, TypeError, binascii.Error, json.JSONDecodeError) as exc:
        raise AppError(400, "invalid_cursor", "The cursor is invalid") from exc


def load_snapshot(revision: PreviewRevision) -> PlanSnapshot:
    try:
        return PlanSnapshot.model_validate(revision.snapshot)
    except ValidationError as exc:
        raise AppError(
            500, "snapshot_invalid", "The stored preview revision is not readable"
        ) from exc


def _maps_urls(lat: float | None, lng: float | None, name: str) -> tuple[str, str]:
    if lat is not None and lng is not None:
        return (
            f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}",
            f"https://maps.apple.com/?daddr={lat},{lng}",
        )
    query = quote(name)
    return (
        f"https://www.google.com/maps/search/?api=1&query={query}",
        f"https://maps.apple.com/?q={query}",
    )


def _unknown_fact(field_code: str) -> PlaceFact:
    return PlaceFact(
        field_code=field_code, knowledge_state="UNKNOWN", freshness="CURRENT", sources=[]
    )


def _fact_schema(fact: FactInfo, today: date) -> PlaceFact:
    verified = fact.verified_at.date() if fact.verified_at else None
    stale = (
        verified is not None
        and fact.stale_after_days is not None
        and verified + timedelta(days=fact.stale_after_days) < today
    )
    value: dict[str, object] | str | None = None
    if fact.knowledge_state == "KNOWN" and fact.value is not None:
        value = fact.value
    return PlaceFact(
        place_fact_id=fact.id,
        field_code=fact.field_code,
        knowledge_state=fact.knowledge_state,
        value=value,
        verified_at=verified,
        valid_until=fact.valid_until,
        freshness="STALE" if stale else "CURRENT",
        sources=[
            Citation(
                source_revision_id=source.source_revision_id,
                place_fact_id=fact.id,
                publisher=source.publisher,
                title=source.title,
                locator=source.locator,
                verified_at=verified,
            )
            for source in fact.sources
            if verified is not None
        ],
    )


class TripService:
    """Owner-scoped trip and preview operations for one authenticated account."""

    def __init__(self, store: TripStore, account_id: uuid.UUID) -> None:
        self.store = store
        self.account_id = account_id

    # -- helpers -------------------------------------------------------------------------------

    async def resolve_locale(self, requested: Locale | None) -> Locale:
        if requested is not None:
            return requested
        stored = await self.store.get_account_locale(self.account_id)
        return "en" if stored == "en" else "vi"

    async def owned_trip(self, trip_id: uuid.UUID, *, for_update: bool = False) -> Trip:
        trip = await self.store.get_trip(self.account_id, trip_id, for_update=for_update)
        if trip is None:
            raise not_found("Trip not found")
        return trip

    async def owned_preview(
        self, preview_id: uuid.UUID, *, for_update: bool = False
    ) -> PlanPreview:
        preview = await self.store.get_preview(self.account_id, preview_id, for_update=for_update)
        if preview is None:
            raise not_found("Preview not found")
        return preview

    async def _time_zone(self, city_id: uuid.UUID) -> tuple[CityInfo | None, str]:
        city = await self.store.get_city(city_id)
        return city, city.time_zone if city is not None else DEFAULT_TIME_ZONE

    @staticmethod
    def _ensure_open(preview: PlanPreview, now: datetime | None = None) -> None:
        moment = now or datetime.now(UTC)
        if preview.status in ("SAVED", "DISCARDED"):
            raise AppError(410, "preview_closed", "This preview is already saved or discarded")
        if preview.status == "EXPIRED" or preview.expires_at <= moment:
            raise AppError(410, "preview_expired", "This preview has expired")

    # -- trips ---------------------------------------------------------------------------------

    async def list_trips(
        self, *, status: str | None, sort: TripSort, cursor: str | None, limit: int
    ) -> TripPage:
        after = decode_cursor(cursor, sort) if cursor else None
        rows = await self.store.list_trips(
            self.account_id, status=status, sort=sort, after=after, limit=limit + 1
        )
        page = rows[:limit]
        next_cursor = encode_cursor(sort, page[-1]) if len(rows) > limit and page else None
        return TripPage(
            next_cursor=next_cursor,
            items=[TripSchema.model_validate(trip, from_attributes=True) for trip in page],
        )

    async def _replay(self, operation: str, key: str, fingerprint: str) -> IdempotentResult | None:
        """Claim ``key`` in the caller's transaction; a stored response means replay (or 409)."""
        existing = await self.store.claim_idempotency(
            self.account_id, operation, key, fingerprint, idempotency.expires_at()
        )
        if existing is None:
            return None
        stored = idempotency.replay_or_raise(existing, fingerprint)
        return IdempotentResult(body=stored.body, replayed=True, status=stored.status)

    async def create_trip(self, body: TripCreate, raw_key: str | None = None) -> IdempotentResult:
        """API-013. An optional ``Idempotency-Key`` (TRIP_CREATE) replays the stored 201 body."""
        key = idempotency.normalize_key(raw_key, required=False)
        try:
            if key is not None:
                fingerprint = idempotency.request_fingerprint(
                    self.account_id, body.model_dump(mode="json")
                )
                replay = await self._replay(idempotency.OP_TRIP_CREATE, key, fingerprint)
                if replay is not None:
                    await self.store.rollback()
                    return replay
            city = await self.store.get_city(body.city_id)
            if city is None or not city.is_enabled:
                raise validation_failed(
                    "unsupported_request",
                    "Gonarra plans 1 to 3 days in one launch city.",
                    city_id=str(body.city_id),
                )
            trip = await self.store.add_trip(
                Trip(
                    account_id=self.account_id,
                    city_id=city.id,
                    title=body.title,
                    start_date=body.start_date,
                    day_count=body.day_count,
                    status="DRAFT",
                    revision=0,
                    planning_preferences={},
                )
            )
            response = TripSchema.model_validate(trip, from_attributes=True).model_dump(mode="json")
            if key is not None:
                await self.store.complete_idempotency(
                    self.account_id,
                    idempotency.OP_TRIP_CREATE,
                    key,
                    status=201,
                    body=response,
                    resource_id=trip.id,
                )
            await self.store.commit()
        except BaseException:
            await self.store.rollback()
            raise
        return IdempotentResult(body=response, replayed=False, status=201)

    async def trip_detail(self, trip: Trip, locale: Locale) -> TripDetail:
        _, time_zone = await self._time_zone(trip.city_id)
        saved = await self.store.saved_itinerary(trip.id)
        days = await render_days(
            self.store,
            saved.snapshot,
            locale=locale,
            start_date=trip.start_date,
            time_zone=time_zone,
            trip_day_ids=saved.trip_day_ids,
        )
        preferences = (
            PlanningPreferences.model_validate(trip.planning_preferences)
            if trip.planning_preferences
            else None
        )
        return TripDetail(
            **TripSchema.model_validate(trip, from_attributes=True).model_dump(),
            planning_preferences=preferences,
            days=days,
            active_preview_id=await self.store.active_preview_id(trip.id),
        )

    async def get_trip(self, trip_id: uuid.UUID, locale: Locale | None) -> TripDetail:
        trip = await self.owned_trip(trip_id)
        return await self.trip_detail(trip, await self.resolve_locale(locale))

    async def update_trip(self, trip_id: uuid.UUID, body: TripUpdate) -> TripSchema:
        """Title only. ``revision`` is the saved-itinerary version and moves only on Save
        (ck_trips_saved_revision), so a title change checks it but does not advance it."""
        try:
            trip = await self.owned_trip(trip_id, for_update=True)
            if body.expected_revision != trip.revision:
                raise revision_conflict(
                    "The trip changed since it was loaded.",
                    expected_revision=body.expected_revision,
                    current_revision=trip.revision,
                )
            trip = await self.store.update_trip_title(trip, body.title)
            await self.store.commit()
        except BaseException:
            await self.store.rollback()
            raise
        return TripSchema.model_validate(trip, from_attributes=True)

    async def delete_trip(self, trip_id: uuid.UUID, expected_revision: int) -> None:
        try:
            trip = await self.owned_trip(trip_id, for_update=True)
            if expected_revision != trip.revision:
                raise revision_conflict(
                    "The trip changed since it was loaded.",
                    expected_revision=expected_revision,
                    current_revision=trip.revision,
                )
            await self.store.delete_trip(trip)
            await self.store.commit()
        except BaseException:
            await self.store.rollback()
            raise

    # -- place card ----------------------------------------------------------------------------

    async def place_card(
        self, trip_id: uuid.UUID, stop_id: uuid.UUID, locale: Locale | None
    ) -> PlaceCard:
        trip = await self.owned_trip(trip_id)
        saved = await self.store.saved_itinerary(trip.id)
        stop = next((s for s in saved.snapshot.all_stops() if s.id == stop_id), None)
        if stop is None:
            raise not_found("Stop not found")
        if stop.trust_level == "WEB_UNVERIFIED":
            assert stop.web_place_candidate_id is not None
            candidate = (await self.store.candidates({stop.web_place_candidate_id})).get(
                stop.web_place_candidate_id
            )
            if candidate is None:
                raise not_found("Stop not found")
            name_vi, name_en, _ = candidate_names(candidate, "vi")
            point = parse_point(candidate.location)
            google, apple = _maps_urls(
                point.latitude if point else None, point.longitude if point else None, name_vi
            )
            return PlaceCard(
                stop_id=stop.id,
                trust_level="WEB_UNVERIFIED",
                place_id=None,
                catalog_publication_id=None,
                web_source=WebSource(
                    url=candidate.source_url,
                    fetched_at=candidate.fetched_at,
                    candidate_id=candidate.id,
                ),
                name_vi=name_vi,
                name_en=name_en,
                address_vi=_unknown_fact(ADDRESS_FIELD),
                entrance=_unknown_fact(ENTRANCE_FIELD),
                directions=Directions(
                    target="PLACE_POSITION", google_maps_url=google, apple_maps_url=apple
                ),
            )

        assert stop.catalog_publication_id is not None
        publication = (await self.store.publications({stop.catalog_publication_id})).get(
            stop.catalog_publication_id
        )
        if publication is None:
            raise not_found("Stop not found")
        facts = {
            fact.field_code: fact
            for fact in await self.store.publication_facts(
                publication.id, (ADDRESS_FIELD, ENTRANCE_FIELD)
            )
        }
        today = datetime.now(UTC).date()
        address = (
            _fact_schema(facts[ADDRESS_FIELD], today)
            if ADDRESS_FIELD in facts
            else _unknown_fact(ADDRESS_FIELD)
        )
        entrance = (
            _fact_schema(facts[ENTRANCE_FIELD], today)
            if ENTRANCE_FIELD in facts
            else _unknown_fact(ENTRANCE_FIELD)
        )
        entrance_value = entrance.value if isinstance(entrance.value, dict) else None
        if entrance.knowledge_state == "KNOWN" and entrance_value is not None:
            target = "ENTRANCE"
            lat = float(str(entrance_value["lat"]))
            lng = float(str(entrance_value["lng"]))
        else:
            target = "PLACE_POSITION"
            point = parse_point(publication.location)
            lat = point.latitude if point else None  # type: ignore[assignment]
            lng = point.longitude if point else None  # type: ignore[assignment]
        google, apple = _maps_urls(lat, lng, publication.name_vi)
        attributions: dict[str, Attribution] = {}
        for fact in facts.values():
            for source in fact.sources:
                if source.attribution_text:
                    attributions.setdefault(
                        source.publisher,
                        Attribution(
                            publisher=source.publisher,
                            attribution_text=source.attribution_text,
                            license_code=source.license_code,
                            homepage_url=source.homepage_url,
                        ),
                    )
        return PlaceCard(
            stop_id=stop.id,
            trust_level="VERIFIED",
            place_id=publication.place_id,
            catalog_publication_id=publication.id,
            name_vi=publication.name_vi,
            name_en=publication.name_en,
            address_vi=address,
            entrance=entrance,
            directions=Directions(
                target=target,
                google_maps_url=google,
                apple_maps_url=apple,
            ),
            attributions=list(attributions.values()),
        )

    # -- handoff -------------------------------------------------------------------------------

    async def handoff_link(
        self,
        trip_id: uuid.UUID,
        *,
        kind: HandoffKind,
        stop_id: uuid.UUID | None,
        partner: PartnerKey | None,
        locale: Locale | None,
    ) -> HandoffLink:
        trip = await self.owned_trip(trip_id)
        resolved_locale = await self.resolve_locale(locale)
        if trip.status != "SAVED" or trip.start_date is None:
            raise AppError(409, "trip_not_saved", "Save the trip before opening a partner")
        city = await self.store.get_city(trip.city_id)
        if city is None:
            raise not_found("Trip not found")
        activity_name: str | None = None
        if kind == "ACTIVITY":
            if stop_id is None:
                raise validation_failed(
                    "validation_error",
                    "stop_id is required for ACTIVITY",
                    fields=[{"location": ["query", "stop_id"]}],
                )
            saved = await self.store.saved_itinerary(trip.id)
            days = await render_days(
                self.store, saved.snapshot, locale="en", start_date=trip.start_date
            )
            stop = next((s for day in days for s in day.stops if s.id == stop_id), None)
            if stop is None:
                raise not_found("Stop not found")
            activity_name = stop.name
        return build_handoff_link(
            kind=kind,
            partner_key=partner,
            trip=HandoffTrip(
                city_id=city.id,
                city_name_en=city.name_en,
                city_code=city.code,
                start_date=trip.start_date,
                day_count=trip.day_count,
            ),
            locale=resolved_locale,
            activity_name=activity_name,
        )

    # -- previews ------------------------------------------------------------------------------

    async def _preview_schema(
        self, preview: PlanPreview, revision: PreviewRevision, locale: Locale
    ) -> PlanPreviewSchema:
        trip = await self.owned_trip(preview.trip_id)
        _, time_zone = await self._time_zone(trip.city_id)
        snapshot = load_snapshot(revision)
        _, reasons = evaluate_health(snapshot)
        days = await render_days(
            self.store,
            snapshot,
            locale=locale,
            start_date=trip.start_date,
            time_zone=time_zone,
        )
        return PlanPreviewSchema(
            id=preview.id,
            trip_id=preview.trip_id,
            base_trip_revision=preview.base_trip_revision,
            head_revision=preview.head_revision,
            preview_revision=revision.preview_revision,
            parent_revision=revision.parent_revision,
            status=preview.status,
            origin=revision.origin,
            plan_health=revision.plan_health,
            health_reasons=reasons,
            expires_at=preview.expires_at,
            days=days,
            assumptions=localize_assumptions(snapshot.assumptions, locale),
            planning_preferences=snapshot.preferences,
            research_used=snapshot.research_used,
            model_version=revision.model_version,
            prompt_version=revision.prompt_version,
            corpus_revision=revision.corpus_revision,
            created_at=revision.created_at,
        )

    async def get_preview(
        self, preview_id: uuid.UUID, revision: int | None, locale: Locale | None
    ) -> PlanPreviewSchema:
        preview = await self.owned_preview(preview_id)
        if preview.status in ("DISCARDED", "EXPIRED"):
            raise AppError(
                410,
                "preview_expired" if preview.status == "EXPIRED" else "preview_closed",
                "This preview is no longer available",
            )
        number = revision if revision is not None else preview.head_revision
        if number < 1 or number > preview.head_revision:
            raise not_found("Preview revision not found")
        row = await self.store.get_revision(preview.id, number)
        if row is None:
            raise not_found("Preview revision not found")
        return await self._preview_schema(preview, row, await self.resolve_locale(locale))

    async def edit_preview(
        self,
        preview_id: uuid.UUID,
        body: PlanPreviewEdit,
        locale: Locale | None = None,
        raw_key: str | None = None,
    ) -> IdempotentResult:
        """Append a MANUAL_EDIT revision against ``expected_revision`` (optimistic, ADR-009).

        Order: owner → idempotency replay (PREVIEW_EDIT, optional key) → open → expected revision.
        The replay check precedes the revision check, so a retried edit whose first attempt
        succeeded answers the stored 200 instead of 409 ``revision_conflict``.
        """
        key = idempotency.normalize_key(raw_key, required=False)
        await self.owned_preview(preview_id)
        try:
            if key is not None:
                fingerprint = idempotency.request_fingerprint(
                    preview_id, body.model_dump(mode="json")
                )
                replay = await self._replay(idempotency.OP_PREVIEW_EDIT, key, fingerprint)
                if replay is not None:
                    await self.store.rollback()
                    return replay
            preview = await self.owned_preview(preview_id, for_update=True)
            self._ensure_open(preview)
            if body.expected_revision != preview.head_revision:
                raise revision_conflict(
                    "The preview changed since it was loaded.",
                    expected_revision=body.expected_revision,
                    current_revision=preview.head_revision,
                )
            trip = await self.owned_trip(preview.trip_id)
            parent = await self.store.get_revision(preview.id, preview.head_revision)
            if parent is None:
                raise not_found("Preview revision not found")
            place_ids = {
                edit.place_id
                for edit in body.edits
                if edit.op in ("ADD_STOP", "REPLACE_STOP") and edit.place_id is not None
            }
            publications = await self.store.published_places(place_ids, trip.city_id)
            parent_snapshot = load_snapshot(parent)
            modes = (
                parent_snapshot.preferences.allowed_modes
                if parent_snapshot.preferences is not None
                and parent_snapshot.preferences.allowed_modes
                else trip.planning_preferences.get("allowed_modes")
            ) or ["WALK"]
            default_mode: TravelMode = "DRIVE" if modes[0] == "DRIVE" else "WALK"
            snapshot, health = apply_edits(
                parent_snapshot,
                body.edits,
                day_count=trip.day_count,
                default_mode=default_mode,
                publications=publications,
            )
            revision = await self.store.append_revision(
                preview,
                PreviewRevision(
                    plan_preview_id=preview.id,
                    preview_revision=preview.head_revision + 1,
                    parent_revision=preview.head_revision,
                    origin="MANUAL_EDIT",
                    plan_health=health,
                    snapshot=snapshot.model_dump(mode="json"),
                    model_version=None,
                    prompt_version=None,
                    corpus_revision=parent.corpus_revision,
                ),
            )
            schema = await self._preview_schema(
                preview, revision, await self.resolve_locale(locale)
            )
            response = schema.model_dump(mode="json")
            if key is not None:
                await self.store.complete_idempotency(
                    self.account_id,
                    idempotency.OP_PREVIEW_EDIT,
                    key,
                    status=200,
                    body=response,
                    resource_id=preview.id,
                )
            await self.store.commit()
        except BaseException:
            await self.store.rollback()
            raise
        return IdempotentResult(body=response, replayed=False)

    async def discard_preview(self, preview_id: uuid.UUID) -> None:
        try:
            preview = await self.owned_preview(preview_id, for_update=True)
            if preview.status == "ACTIVE":
                await self.store.set_preview_status(preview, "DISCARDED")
            await self.store.commit()
        except BaseException:
            await self.store.rollback()
            raise

    # -- Save ----------------------------------------------------------------------------------

    async def accept_preview(
        self,
        preview_id: uuid.UUID,
        body: AcceptPreviewRequest,
        raw_key: str | None,
        locale: Locale | None = None,
    ) -> AcceptResult:
        """Save (API-022): promote the head revision into the trip in one transaction.

        Order: owner → idempotency replay → preview open → both expected revisions → health not
        BLOCKED → publication eligibility → WEB_UNVERIFIED acknowledgement → replace itinerary.
        """
        key = idempotency.normalize_key(raw_key, required=True)
        assert key is not None
        await self.owned_preview(preview_id)
        fingerprint = idempotency.request_fingerprint(preview_id, body.model_dump(mode="json"))
        try:
            existing = await self.store.claim_idempotency(
                self.account_id,
                idempotency.OP_TRIP_SAVE,
                key,
                fingerprint,
                idempotency.expires_at(),
            )
            if existing is not None:
                stored = idempotency.replay_or_raise(existing, fingerprint)
                await self.store.rollback()
                return AcceptResult(body=stored.body, replayed=True)

            preview = await self.owned_preview(preview_id, for_update=True)
            trip = await self.owned_trip(preview.trip_id, for_update=True)
            self._ensure_open(preview)
            if body.expected_preview_revision != preview.head_revision:
                raise revision_conflict(
                    "The preview changed since it was loaded.",
                    expected_preview_revision=body.expected_preview_revision,
                    current_revision=preview.head_revision,
                )
            if body.expected_trip_revision != trip.revision:
                raise revision_conflict(
                    "The trip changed since this preview was opened.",
                    expected_trip_revision=body.expected_trip_revision,
                    current_revision=trip.revision,
                )
            if preview.base_trip_revision != trip.revision:
                raise revision_conflict(
                    "The trip was saved from another preview after this one was opened.",
                    base_trip_revision=preview.base_trip_revision,
                    current_revision=trip.revision,
                )
            revision = await self.store.get_revision(preview.id, preview.head_revision)
            if revision is None:
                raise not_found("Preview revision not found")
            snapshot = load_snapshot(revision)
            if revision.plan_health == "BLOCKED":
                _, reasons = evaluate_health(snapshot)
                raise AppError(
                    409,
                    "plan_blocked",
                    "Plan Health is BLOCKED; fix the plan before saving.",
                    context={"reasons": [reason.model_dump(mode="json") for reason in reasons]},
                )
            if any(day.day_index > trip.day_count for day in snapshot.days):
                raise validation_failed(
                    "unsupported_request",
                    "The preview has more days than the trip.",
                    day_count=trip.day_count,
                )
            await self._check_publications(snapshot)
            if snapshot.has_web_unverified() and not body.acknowledge_web_unverified:
                raise validation_failed(
                    "web_unverified_acknowledgement_required",
                    "This plan contains a place found on the web that is not verified; "
                    "confirm before saving.",
                    stop_ids=[
                        str(stop.id)
                        for stop in snapshot.all_stops()
                        if stop.trust_level == "WEB_UNVERIFIED"
                    ],
                )
            trip = await self.store.replace_itinerary(trip, snapshot)
            await self.store.set_preview_status(preview, "SAVED")
            detail = await self.trip_detail(trip, await self.resolve_locale(locale))
            response = detail.model_dump(mode="json")
            await self.store.complete_idempotency(
                self.account_id,
                idempotency.OP_TRIP_SAVE,
                key,
                status=200,
                body=response,
                resource_id=trip.id,
            )
            await self.store.commit()
        except BaseException:
            await self.store.rollback()
            raise
        return AcceptResult(body=response, replayed=False)

    async def _check_publications(self, snapshot: PlanSnapshot) -> None:
        stops = snapshot.all_stops()
        publication_ids = {
            s.catalog_publication_id for s in stops if s.catalog_publication_id is not None
        }
        candidate_ids = {
            s.web_place_candidate_id for s in stops if s.web_place_candidate_id is not None
        }
        publications = await self.store.publications(publication_ids)
        candidates = await self.store.candidates(candidate_ids)
        missing = [
            str(stop.id)
            for stop in stops
            if (
                stop.catalog_publication_id is not None
                and (
                    (info := publications.get(stop.catalog_publication_id)) is None
                    or info.state != "PUBLISHED"
                    or info.place_id != stop.place_id
                )
            )
            or (
                stop.web_place_candidate_id is not None
                and stop.web_place_candidate_id not in candidates
            )
        ]
        if missing:
            raise validation_failed(
                "publication_incomplete",
                "Some places are no longer published; edit the plan before saving.",
                missing=missing,
            )

    # -- deletion ------------------------------------------------------------------------------

    async def request_deletion(self) -> tuple[AccountDeletionStatus, bool]:
        """Idempotent by state: an open job (REQUESTED, IN_PROGRESS, FAILED) is returned as is."""
        try:
            job = await self.store.open_deletion_job(self.account_id)
            created = job is None
            if job is None:
                job = await self.store.add_deletion_job(self.account_id)
            await self.store.commit()
        except BaseException:
            await self.store.rollback()
            raise
        return deletion_status(job), created

    async def deletion_status(self) -> AccountDeletionStatus:
        job = await self.store.latest_deletion_job(self.account_id)
        if job is None:
            raise not_found("No deletion was requested")
        return deletion_status(job)


def deletion_status(job: AccountDeletionJob) -> AccountDeletionStatus:
    return AccountDeletionStatus.model_validate(job, from_attributes=True)

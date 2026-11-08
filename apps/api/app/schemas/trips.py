"""Trips, plan previews, Save, handoff and deletion schemas (openapi.yaml 0.4.0, CMP-007/008/011).

Names follow ``docs/04-design/api/openapi.yaml``. Additions the 0.4.0 contract lacks (architecture
§5 trust label contract, OQ-128 acknowledgement) are marked "extension" in the field description.
"""

import datetime as dt
import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Locale = Literal["vi", "en"]
TravelMode = Literal["WALK", "DRIVE"]
Pace = Literal["RELAXED", "BALANCED", "PACKED"]
TripStatus = Literal["DRAFT", "SAVED"]
PlanHealth = Literal["GOOD", "WARNING", "BLOCKED"]
TrustLevel = Literal["VERIFIED", "WEB_UNVERIFIED"]
LegAvailability = Literal["AVAILABLE", "UNAVAILABLE", "EXPIRED"]
PreviewStatus = Literal["ACTIVE", "SAVED", "DISCARDED", "EXPIRED"]
PreviewOrigin = Literal["GENERATED", "MANUAL_EDIT", "DAY_REGENERATED", "REPAIRED"]
ConflictType = Literal[
    "CLOSED_AT_PLANNED_TIME",
    "LEG_UNAVAILABLE",
    "DAY_WINDOW_EXCEEDED",
    "OPENING_HOURS_UNKNOWN",
    "FACT_STALE",
    "MUST_SEE_NOT_INCLUDED",
    "CLOSED_ON_DATE",
    "LEG_MODE_RESTRICTED",
    "LUNAR_EVENT_CONFLICT",
    "TICKET_VALIDITY",
    "SEASONAL_WARNING",
    "WEB_PLACE_UNVERIFIED",
    "WEB_PLACE_UNRESOLVED",
    "LEG_ESTIMATED",
]
ConflictSeverity = Literal["BLOCKING", "WARNING", "INFO"]
LocalTime = Annotated[str, Field(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$", examples=["08:00"])]
Title = Annotated[str, Field(max_length=120)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---- Shared value types ----------------------------------------------------------------------


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Conflict(BaseModel):
    type: ConflictType = Field(
        description=(
            "Plan Health conflict type (ADR-011). LEG_ESTIMATED (INFO, openapi 1.0.2) marks a leg "
            "whose distance/duration is a demo estimate, not a Google Routes measurement."
        )
    )
    severity: ConflictSeverity = Field(
        description=(
            "BLOCKING → plan BLOCKED; WARNING → plan at most WARNING; INFO is a notice only and "
            "never changes plan_health."
        )
    )
    message: str | None = None
    rule_id: uuid.UUID | None = Field(
        default=None, description="place_closure_rules row behind a calendar conflict."
    )
    date: dt.date | None = Field(default=None, description="Trip date the conflict applies to.")
    stop_ids: list[uuid.UUID] = Field(default_factory=list, description="Stops involved.")


class WebSource(BaseModel):
    """Provenance of a WEB_UNVERIFIED stop (architecture §5 trust label contract)."""

    url: str
    fetched_at: datetime
    candidate_id: uuid.UUID


# ---- Trips -----------------------------------------------------------------------------------


class TripCreate(_Strict):
    city_id: uuid.UUID
    title: Title | None = None
    start_date: date
    day_count: int = Field(ge=1, le=3)


class TripUpdate(_Strict):
    expected_revision: int = Field(ge=0)
    title: Title | None = None


class Trip(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    title: str | None = None
    start_date: date | None
    day_count: int = Field(ge=1, le=3)
    status: TripStatus
    revision: int = Field(ge=0)
    saved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TripPage(BaseModel):
    next_cursor: str | None = Field(description="Null on the last page.")
    items: list[Trip]


class PlanningPreferences(_Strict):
    pace: Pace | None = None
    interest_category_codes: list[str] | None = Field(default=None, max_length=20)
    allowed_modes: list[TravelMode] | None = Field(default=None, min_length=1)
    day_start_time: LocalTime | None = None
    day_end_time: LocalTime | None = None
    must_see_place_ids: list[uuid.UUID] | None = Field(default=None, max_length=10)


class Stop(BaseModel):
    id: uuid.UUID = Field(
        description="Stable across preview revisions and into the saved trip_stops row."
    )
    trust_level: TrustLevel = Field(description="Extension (architecture §5, DEC-015).")
    place_id: uuid.UUID | None = Field(description="Null for a WEB_UNVERIFIED stop.")
    catalog_publication_id: uuid.UUID | None = Field(description="Null for a WEB_UNVERIFIED stop.")
    web_source: WebSource | None = Field(
        default=None, description="Extension: present only for a WEB_UNVERIFIED stop."
    )
    ordinal: int = Field(ge=1)
    planned_arrival: datetime | None = None
    planned_departure: datetime | None = None
    visit_minutes: int = Field(ge=1)
    is_locked: bool
    name_vi: str
    name: str
    location: GeoPoint | None = Field(
        description="Null only for a WEB_UNVERIFIED stop without coordinates."
    )
    rationale: str | None = None
    conflicts: list[Conflict] = Field(default_factory=list)


class Leg(BaseModel):
    from_stop_id: uuid.UUID
    to_stop_id: uuid.UUID
    travel_mode: TravelMode
    availability: LegAvailability
    distance_m: int | None = None
    duration_s: int | None = None
    measured_at: datetime | None = None
    estimated: bool = Field(
        default=False,
        description=(
            "True when distance_m/duration_s are a straight-line demo estimate (owner demo without "
            "Google Routes), not a measurement. Such legs also carry a LEG_ESTIMATED conflict."
        ),
    )
    conflicts: list[Conflict] = Field(default_factory=list)


class ItineraryDay(BaseModel):
    trip_day_id: uuid.UUID | None = Field(
        default=None, description="Null inside a preview snapshot."
    )
    day_index: int = Field(ge=1, le=3)
    day_window_start: LocalTime
    day_window_end: LocalTime
    stops: list[Stop]
    legs: list[Leg]


class TripDetail(Trip):
    planning_preferences: PlanningPreferences | None = None
    days: list[ItineraryDay] = Field(description="Saved itinerary; empty for a DRAFT trip.")
    active_preview_id: uuid.UUID | None = None


# ---- Place card ------------------------------------------------------------------------------


class Citation(BaseModel):
    source_revision_id: uuid.UUID
    knowledge_chunk_id: uuid.UUID | None = None
    section: str | None = None
    place_fact_id: uuid.UUID | None = None
    publisher: str
    title: str | None = None
    locator: str | None = None
    verified_at: date


class PlaceFact(BaseModel):
    place_fact_id: uuid.UUID | None = None
    field_code: str
    knowledge_state: Literal["KNOWN", "UNKNOWN", "NOT_APPLICABLE"]
    value: dict[str, object] | str | None = None
    verified_at: date | None = None
    valid_until: date | None = None
    freshness: Literal["CURRENT", "STALE"]
    sources: list[Citation]


class Directions(BaseModel):
    target: Literal["ENTRANCE", "PLACE_POSITION"]
    google_maps_url: str
    apple_maps_url: str


class Attribution(BaseModel):
    publisher: str
    attribution_text: str
    license_code: str | None = None
    homepage_url: str | None = None


class PlaceCard(BaseModel):
    stop_id: uuid.UUID
    trust_level: TrustLevel = Field(description="Extension (architecture §5).")
    place_id: uuid.UUID | None
    catalog_publication_id: uuid.UUID | None = None
    web_source: WebSource | None = Field(default=None, description="Extension.")
    name_vi: str
    name_en: str
    address_vi: PlaceFact
    entrance: PlaceFact
    directions: Directions
    attributions: list[Attribution] = Field(default_factory=list)


# ---- Planning --------------------------------------------------------------------------------


class PlanPreviewCreate(_Strict):
    source: Literal["GENERATE", "SAVED_ITINERARY"]
    expected_trip_revision: int = Field(ge=0)
    locale: Locale
    request_text: str | None = Field(default=None, max_length=1000)
    preferences: PlanningPreferences | None = None


class PlanPreview(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    base_trip_revision: int
    head_revision: int
    preview_revision: int = Field(description="Revision represented by this body.")
    parent_revision: int | None = None
    status: PreviewStatus
    origin: PreviewOrigin
    plan_health: PlanHealth
    health_reasons: list[Conflict] = Field(default_factory=list)
    expires_at: datetime
    days: list[ItineraryDay]
    assumptions: list[str] = Field(default_factory=list)
    research_used: bool = Field(default=False, description="Extension (architecture §5).")
    model_version: str | None = None
    prompt_version: str | None = None
    corpus_revision: int | None = None
    created_at: datetime


EditOp = Literal[
    "MOVE_STOP",
    "ADD_STOP",
    "REMOVE_STOP",
    "REPLACE_STOP",
    "SET_VISIT_MINUTES",
    "SET_LEG_MODE",
    "LOCK_STOP",
    "UNLOCK_STOP",
]


class PreviewEditOperation(_Strict):
    op: EditOp
    stop_id: uuid.UUID | None = None
    day_index: int | None = Field(default=None, ge=1, le=3)
    to_ordinal: int | None = Field(default=None, ge=1)
    place_id: uuid.UUID | None = Field(
        default=None,
        description="ADD_STOP / REPLACE_STOP; must be published in the trip's city.",
    )
    visit_minutes: int | None = Field(default=None, ge=5, le=600)
    from_stop_id: uuid.UUID | None = None
    to_stop_id: uuid.UUID | None = None
    travel_mode: TravelMode | None = None


class PlanPreviewEdit(_Strict):
    expected_revision: int = Field(ge=1)
    edits: list[PreviewEditOperation] = Field(min_length=1, max_length=20)


class RegenerateDayRequest(_Strict):
    expected_revision: int = Field(ge=1)
    day_index: int = Field(ge=1, le=3)
    locked_stop_ids: list[uuid.UUID] | None = None
    instruction: str | None = Field(default=None, max_length=500)
    locale: Locale | None = None


class AcceptPreviewRequest(_Strict):
    expected_preview_revision: int = Field(ge=1)
    expected_trip_revision: int = Field(ge=0)
    acknowledge_web_unverified: bool = Field(
        default=False,
        description=(
            "Extension (OQ-128, ADR-009): must be true when the revision contains a "
            "WEB_UNVERIFIED stop, otherwise 422 web_unverified_acknowledgement_required."
        ),
    )


# ---- Stays -----------------------------------------------------------------------------------

HandoffKind = Literal["STAY", "ACTIVITY", "TRANSPORT"]
PartnerKey = Literal["agoda", "booking_com", "klook", "twelve_go"]


class HandoffLink(BaseModel):
    kind: HandoffKind
    partner_key: PartnerKey
    partner_display_name: str
    url: str
    city_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None


# ---- Identity: deletion ----------------------------------------------------------------------


class AccountDeletionRequest(_Strict):
    confirm: Literal[True]


class AccountDeletionStatus(BaseModel):
    id: uuid.UUID
    status: Literal["REQUESTED", "IN_PROGRESS", "COMPLETED", "FAILED"]
    attempt_count: int = Field(ge=0)
    failure_reason: str | None = None
    requested_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

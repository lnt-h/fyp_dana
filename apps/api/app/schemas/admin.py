"""Curator (``/v1/admin``) request and response schemas.

Mirrors the 0.4.0 admin components of ``docs/04-design/api/openapi.yaml`` and adds the 1.0
curator surfaces (web-candidate queue, facts, closure rules, chunks, source revisions).
Write schemas forbid unknown fields; DB CHECK vocabularies are expressed as ``Literal``.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Locale = Literal["vi", "en"]
WorkflowState = Literal[
    "IMPORTED", "MATCH_REVIEW", "CONTENT_REVIEW", "READY_TO_PUBLISH", "PUBLISHED", "RETIRED"
]
ReviewableWorkflowState = Literal[
    "IMPORTED", "MATCH_REVIEW", "CONTENT_REVIEW", "READY_TO_PUBLISH", "RETIRED"
]
KnowledgeState = Literal["KNOWN", "UNKNOWN", "NOT_APPLICABLE"]
TranslationOrigin = Literal["ORIGINAL", "HUMAN_TRANSLATION", "AI_DRAFT"]
LocalizationReviewState = Literal["DRAFT", "APPROVED", "REJECTED", "SUPERSEDED"]
AliasKind = Literal["NAME", "ALIAS"]
AliasReviewState = Literal["DRAFT", "APPROVED", "REJECTED"]
FactReviewState = Literal["DRAFT", "APPROVED", "REJECTED", "SUPERSEDED"]
ConflictState = Literal["NONE", "OPEN", "RESOLVED"]
ChunkSection = Literal["OVERVIEW", "HISTORY", "HIGHLIGHTS", "VISIT_TIPS", "ETIQUETTE", "ACCESS"]
ChunkReviewState = Literal["DRAFT", "APPROVED", "RETIRED"]
EmbeddingState = Literal["EMBEDDED", "PENDING"]
PublicationState = Literal["PUBLISHED", "SUPERSEDED", "WITHDRAWN"]
SourceKind = Literal["OFFICIAL", "OPEN_DATA", "REFERENCE", "OWN_OBSERVATION", "WEB"]
CuratorSourceKind = Literal["OFFICIAL", "OPEN_DATA", "REFERENCE", "OWN_OBSERVATION"]
ClosureAppliesTo = Literal["PLACE", "AREA", "CITY"]
ClosureRuleKind = Literal["WEEKLY", "DATE", "LUNAR_DATE", "SEASON", "TICKET_VALIDITY"]
ClosureEffect = Literal["CLOSED", "PARTIAL", "EVENT", "NOTICE"]
ClosureSeverity = Literal["BLOCKING", "WARNING"]
ClosureReviewState = Literal["DRAFT", "APPROVED", "RETIRED"]
WebCandidateReviewState = Literal["PENDING", "PROMOTED", "REJECTED", "EXPIRED"]
PlacesCheckOutcome = Literal[
    "EXISTS_OPERATIONAL", "EXISTS_CLOSED", "NOT_FOUND", "OUTSIDE_CITY", "SKIPPED"
]
ImportRunStatus = Literal["RUNNING", "SUCCEEDED", "FAILED"]

SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"
CODE_PATTERN = r"^[A-Z][A-Z0-9_]*$"


class _Write(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class PageInfo(BaseModel):
    next_cursor: str | None = Field(description="Null on the last page.")


class ReviewWarning(BaseModel):
    code: str
    knowledge_chunk_id: uuid.UUID | None = None


class GateViolation(BaseModel):
    code: str
    detail: str | None = None


# ---- Candidates -------------------------------------------------------------------------


class CandidateSummary(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    slug: str
    category_code: str | None
    area_code: str | None = None
    workflow_state: WorkflowState
    name_vi: str | None = None
    name_en: str | None = None
    content_revision: int
    has_ai_draft: bool = False
    provider_release: str | None = None
    gate_missing_count: int = Field(ge=0)
    updated_at: datetime


class CandidatePage(PageInfo):
    items: list[CandidateSummary]


class Localization(BaseModel):
    id: uuid.UUID
    locale: Locale
    localization_revision: int
    name: str
    short_description: str | None
    description: str | None
    translation_origin: TranslationOrigin
    review_state: LocalizationReviewState
    reviewed_at: datetime | None


class LocalizationInput(_Write):
    """Without ``id``: a new localization revision. With ``id``: a review decision only."""

    id: uuid.UUID | None = None
    locale: Locale
    name: str | None = Field(default=None, min_length=1, max_length=200)
    short_description: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=4000)
    translation_origin: TranslationOrigin = "ORIGINAL"
    review_state: Literal["DRAFT", "APPROVED", "REJECTED"] = "DRAFT"

    @model_validator(mode="after")
    def _name_for_new_revision(self) -> LocalizationInput:
        if self.id is None and self.name is None:
            raise ValueError("name is required for a new localization revision")
        return self


class Alias(BaseModel):
    id: uuid.UUID
    locale: Locale
    alias_kind: AliasKind
    alias: str
    alias_normalized: str
    review_state: AliasReviewState


class AliasInput(_Write):
    """Upserted by normalized form (lower case, diacritics removed, đ→d)."""

    locale: Locale
    alias: str = Field(min_length=1, max_length=200)
    alias_kind: AliasKind = "ALIAS"
    review_state: AliasReviewState = "DRAFT"


class FactEvidence(BaseModel):
    source_revision_id: uuid.UUID
    supported_claim: str


class FactEvidenceInput(_Write):
    source_revision_id: uuid.UUID
    supported_claim: str = Field(min_length=1, max_length=500)


class AdminPlaceFact(BaseModel):
    id: uuid.UUID
    place_id: uuid.UUID
    field_code: str
    fact_revision: int
    knowledge_state: KnowledgeState
    value: dict[str, Any] | None
    verified_at: datetime | None
    valid_until: date | None
    review_state: FactReviewState
    conflict_state: ConflictState
    conflict_note: str | None
    evidence: list[FactEvidence]
    source_revision_ids: list[uuid.UUID]
    created_at: datetime


class AdminPlaceFactList(BaseModel):
    items: list[AdminPlaceFact]


class FactCreate(_Write):
    """A new DRAFT revision of one fact field. ``value`` is required iff KNOWN."""

    field_code: str = Field(pattern=CODE_PATTERN, max_length=64)
    knowledge_state: KnowledgeState
    value: dict[str, Any] | None = None
    valid_until: date | None = None
    conflict_state: ConflictState = "NONE"
    conflict_note: str | None = Field(default=None, max_length=1000)
    evidence: list[FactEvidenceInput] = Field(default_factory=list, max_length=10)


class FactUpdate(_Write):
    """Edit a DRAFT fact revision; approved revisions are immutable (new revision instead)."""

    knowledge_state: KnowledgeState | None = None
    value: dict[str, Any] | None = None
    valid_until: date | None = None
    conflict_state: ConflictState | None = None
    conflict_note: str | None = Field(default=None, max_length=1000)
    evidence: list[FactEvidenceInput] | None = Field(default=None, max_length=10)


class FactReview(_Write):
    decision: Literal["APPROVE", "REJECT"]
    verified_at: datetime | None = Field(
        default=None, description="When the curator verified the evidence; defaults to now."
    )


class KnowledgeChunk(BaseModel):
    id: uuid.UUID
    place_id: uuid.UUID | None
    locale: Locale
    section: str
    corpus_revision: int
    chunk_index: int
    content: str
    content_sha256: str
    source_revision_ids: list[uuid.UUID]
    review_state: ChunkReviewState
    embedding_state: EmbeddingState
    embedding_model: str | None
    retired_at: datetime | None
    created_at: datetime


class KnowledgeChunkList(BaseModel):
    corpus_revision: int | None = Field(
        description="Working corpus revision of the place (null when it has no chunks)."
    )
    published_corpus_revision: int | None = None
    items: list[KnowledgeChunk]


class ChunkSaveResult(KnowledgeChunk):
    warnings: list[ReviewWarning] = Field(default_factory=list)


class ChunkInput(_Write):
    locale: Locale
    section: ChunkSection
    content: str = Field(
        min_length=1,
        max_length=4000,
        description="Original narrative text; never operational facts (hours, prices, addresses).",
    )
    source_revision_ids: list[uuid.UUID] = Field(min_length=1, max_length=10)
    review_state: Literal["DRAFT", "APPROVED"] = Field(
        default="DRAFT",
        description="APPROVED is applied only when the embedding is stored; else stays DRAFT "
        "with warning CHUNK_APPROVAL_DEFERRED.",
    )


class ChunkUpdate(_Write):
    content: str | None = Field(default=None, min_length=1, max_length=4000)
    source_revision_ids: list[uuid.UUID] | None = Field(default=None, min_length=1, max_length=10)
    review_state: ChunkReviewState | None = None


class CatalogPublication(BaseModel):
    id: uuid.UUID
    place_id: uuid.UUID
    city_id: uuid.UUID
    publication_revision: int
    state: PublicationState
    published_by_account_id: uuid.UUID | None
    published_at: datetime
    state_changed_at: datetime | None
    state_reason: str | None
    corpus_revision: int | None = None


class CandidateDetail(CandidateSummary):
    location: GeoPoint
    visit_minutes_min: int | None
    visit_minutes_suggested: int | None
    visit_minutes_max: int | None
    has_no_media: bool
    localizations: list[Localization]
    aliases: list[Alias]
    facts: list[AdminPlaceFact]
    chunks: list[KnowledgeChunk] = Field(
        description="Chunks of the working corpus revision, one per section and locale."
    )
    gate_violations: list[GateViolation]
    warnings: list[ReviewWarning] = Field(default_factory=list)
    publications: list[CatalogPublication]


class _PlaceAttributes(_Write):
    category_code: str | None = Field(default=None, pattern=CODE_PATTERN)
    area_code: str | None = Field(default=None, pattern=SLUG_PATTERN)
    location: GeoPoint | None = None
    visit_minutes_min: int | None = Field(default=None, ge=5, le=600)
    visit_minutes_suggested: int | None = Field(default=None, ge=5, le=600)
    visit_minutes_max: int | None = Field(default=None, ge=5, le=600)
    has_no_media: bool | None = None


class CandidateCreate(_PlaceAttributes):
    """Manual place draft (curator research sheet). Starts in CONTENT_REVIEW."""

    city_id: uuid.UUID | None = Field(default=None, description="Defaults to the enabled city.")
    slug: str = Field(pattern=SLUG_PATTERN, max_length=120)
    location: GeoPoint
    localizations: list[LocalizationInput] = Field(default_factory=list, max_length=2)
    aliases: list[AliasInput] = Field(default_factory=list, max_length=20)


class CandidateReview(_PlaceAttributes):
    """Partial update against ``expected_content_revision``; increments content_revision.

    An explicit ``null`` clears ``category_code``/``area_code``/visit minutes; absent fields
    are unchanged. Facts are written only through ``/admin/places/{place_id}/facts``.
    """

    expected_content_revision: int = Field(ge=0)
    workflow_state: ReviewableWorkflowState | None = None
    localizations: list[LocalizationInput] | None = Field(default=None, max_length=4)
    aliases: list[AliasInput] | None = Field(default=None, max_length=20)
    chunks: list[ChunkInput] | None = Field(default=None, max_length=12)
    confirm_ai_draft_locales: list[Locale] = Field(default_factory=list)


class PublishRequest(_Write):
    expected_content_revision: int = Field(ge=0)


class UnpublishRequest(_Write):
    state_reason: str = Field(min_length=1, max_length=500)


# ---- Facts, closure rules ---------------------------------------------------------------


class ClosureRule(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    applies_to: ClosureAppliesTo
    place_id: uuid.UUID | None
    area_code: str | None
    rule_kind: ClosureRuleKind
    effect: ClosureEffect
    params: dict[str, Any]
    severity: ClosureSeverity
    note_vi: str
    note_en: str
    effective_from: date | None
    effective_to: date | None
    source_revision_id: uuid.UUID | None
    review_state: ClosureReviewState
    verified_at: datetime | None
    reviewed_by_account_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ClosureRuleList(BaseModel):
    items: list[ClosureRule]


class ClosureRuleCreate(_Write):
    """Params shape by rule_kind (schema.sql place_closure_rules.params):
    WEEKLY {weekdays:[1..7], from?, to?}; DATE {dates:[YYYY-MM-DD]} | {month_day:[MM-DD]};
    LUNAR_DATE {lunar_days:[1..30], lunar_months:[1..12]|null}; SEASON {from_month_day,
    to_month_day}; TICKET_VALIDITY {valid_same_day:true} | {valid_hours:1..168}."""

    applies_to: ClosureAppliesTo = "PLACE"
    city_id: uuid.UUID | None = Field(
        default=None, description="AREA/CITY rules; defaults to the enabled city."
    )
    area_code: str | None = Field(default=None, pattern=SLUG_PATTERN)
    rule_kind: ClosureRuleKind
    effect: ClosureEffect
    params: dict[str, Any] = Field(default_factory=dict)
    severity: ClosureSeverity | None = Field(
        default=None, description="Defaults to BLOCKING for CLOSED, WARNING otherwise."
    )
    note_vi: str = Field(min_length=1, max_length=500)
    note_en: str = Field(min_length=1, max_length=500)
    effective_from: date | None = None
    effective_to: date | None = None
    source_revision_id: uuid.UUID | None = None


class ClosureRuleUpdate(_Write):
    rule_kind: ClosureRuleKind | None = None
    effect: ClosureEffect | None = None
    params: dict[str, Any] | None = None
    severity: ClosureSeverity | None = None
    note_vi: str | None = Field(default=None, min_length=1, max_length=500)
    note_en: str | None = Field(default=None, min_length=1, max_length=500)
    effective_from: date | None = None
    effective_to: date | None = None
    source_revision_id: uuid.UUID | None = None
    review_state: ClosureReviewState | None = Field(
        default=None, description="APPROVED needs a source revision; sets verified_at."
    )
    verified_at: datetime | None = None


# ---- Web candidates ---------------------------------------------------------------------


class WebCandidate(BaseModel):
    id: uuid.UUID
    city_id: uuid.UUID
    trust_label: Literal["WEB_UNVERIFIED"] = "WEB_UNVERIFIED"
    name: str
    name_vi: str | None
    name_en: str | None
    category_guess: str | None
    location: GeoPoint | None
    coordinate_source: str | None
    google_place_id: str | None
    places_check_outcome: PlacesCheckOutcome
    places_checked_at: datetime | None
    source_revision_id: uuid.UUID
    source_locator: str | None = None
    source_publisher: str | None = None
    fetched_at: datetime
    extraction: dict[str, Any]
    extraction_model: str | None
    review_state: WebCandidateReviewState
    promoted_place_id: uuid.UUID | None
    reviewed_by_account_id: uuid.UUID | None
    reviewed_at: datetime | None
    review_note: str | None
    times_proposed: int
    created_at: datetime
    updated_at: datetime


class WebCandidatePage(PageInfo):
    items: list[WebCandidate]


class WebCandidateReview(_Write):
    """APPROVE promotes into a place draft (IMPORTED, never published); REJECT needs a note."""

    decision: Literal["APPROVE", "REJECT"]
    review_note: str | None = Field(default=None, min_length=1, max_length=500)
    slug: str | None = Field(default=None, pattern=SLUG_PATTERN, max_length=120)
    category_code: str | None = Field(default=None, pattern=CODE_PATTERN)
    area_code: str | None = Field(default=None, pattern=SLUG_PATTERN)
    location: GeoPoint | None = Field(
        default=None, description="Required on APPROVE when the candidate has no location."
    )
    name_vi: str | None = Field(default=None, min_length=1, max_length=200)
    name_en: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode="after")
    def _reject_needs_note(self) -> WebCandidateReview:
        if self.decision == "REJECT" and not self.review_note:
            raise ValueError("review_note is required to reject a candidate")
        return self


# ---- Sources, imports, city summary -----------------------------------------------------


class SourceCreate(_Write):
    data_provider_id: uuid.UUID | None = None
    publisher: str = Field(min_length=1, max_length=200)
    source_kind: CuratorSourceKind
    homepage_url: str | None = Field(default=None, max_length=2000, pattern=r"^https?://")
    license_code: str = Field(min_length=1, max_length=100)
    attribution_text: str = Field(min_length=1, max_length=500)


class Source(BaseModel):
    id: uuid.UUID
    data_provider_id: uuid.UUID | None
    publisher: str
    source_kind: SourceKind
    homepage_url: str | None
    license_code: str
    attribution_text: str | None
    created_at: datetime
    updated_at: datetime


class SourcePage(PageInfo):
    items: list[Source]


class SourceRevisionCreate(_Write):
    locator: str = Field(min_length=1, max_length=2000, description="URL or document reference.")
    title: str | None = Field(default=None, max_length=500)
    retrieved_at: datetime
    content_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


class SourceRevision(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    locator: str
    title: str | None
    retrieved_at: datetime
    content_sha256: str | None
    created_at: datetime


class SourceRevisionList(BaseModel):
    items: list[SourceRevision]


class ImportRun(BaseModel):
    id: uuid.UUID
    data_provider_id: uuid.UUID
    provider_key: str | None = None
    provider_policy_id: uuid.UUID
    city_id: uuid.UUID
    release_id: str
    importer_version: str
    status: ImportRunStatus
    record_count: int | None
    accepted_count: int | None
    rejected_count: int | None
    duplicate_count: int | None
    failure_code: str | None
    started_at: datetime
    completed_at: datetime | None


class ImportRunPage(PageInfo):
    items: list[ImportRun]


class AreaCount(BaseModel):
    area_code: str
    published_count: int = Field(ge=0)


class CitySummary(BaseModel):
    city_id: uuid.UUID
    code: str
    is_enabled: bool
    published_count: int = Field(ge=0)
    candidate_count: int = Field(ge=0)
    pending_web_candidate_count: int = Field(ge=0)
    published_by_area: list[AreaCount]


class CitySummaryList(BaseModel):
    items: list[CitySummary]

"""Guide sessions, questions, messages, citations and stream events (API-024..028, ADR-010).

Names and shapes follow ``docs/04-design/api/openapi.yaml`` (``GuideSessionCreate``,
``GuideSession``, ``GuideQuestion``, ``GuideMessage``, ``GuideMessagePage``, ``Citation``,
``GuideStreamEvent``).
"""

import uuid
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.schemas.common import ErrorDetail

Locale = Literal["vi", "en"]
GuideScope = Literal["CITY", "PLACE"]
InputMode = Literal["TEXT", "VOICE_TRANSCRIPT"]
MessageRole = Literal["TRAVELER", "ASSISTANT"]
AnswerStatus = Literal[
    "ANSWERED", "ANSWERED_WEB_UNVERIFIED", "INSUFFICIENT_EVIDENCE", "NOT_RECOGNISED"
]
EvidenceKind = Literal["FACT", "CHUNK", "WEB"]
ChunkSection = Literal["OVERVIEW", "HISTORY", "HIGHLIGHTS", "VISIT_TIPS", "ETIQUETTE", "ACCESS"]
TrustLevel = Literal["VERIFIED", "WEB_UNVERIFIED"]
GuideStage = Literal["VALIDATING", "RETRIEVING", "SEARCHING_WEB", "ANSWERING"]

MAX_QUESTION_CHARS = 4000


class GuideSessionCreate(BaseModel):
    """City-level Guide (scope CITY) or one pinned published place (scope PLACE)."""

    model_config = ConfigDict(extra="forbid")

    scope: GuideScope
    city_code: str | None = Field(default=None, description="Defaults to `da-nang`.")
    place_id: uuid.UUID | None = None
    trip_id: uuid.UUID | None = None
    locale: Locale


class GuideSession(BaseModel):
    id: uuid.UUID
    scope: GuideScope
    city_code: str
    trip_id: uuid.UUID | None = None
    place_id: uuid.UUID | None
    locale: Locale
    expires_at: datetime | None = None
    created_at: datetime


class GuideQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_QUESTION_CHARS),
    ]
    input_mode: InputMode


class Citation(BaseModel):
    """Points to evidence that was supplied to the writer (ADR-010). FACT and CHUNK are VERIFIED
    catalog content; WEB is the labelled WEB_UNVERIFIED fallback (not produced yet)."""

    source_revision_id: uuid.UUID
    trust_level: TrustLevel
    evidence_kind: EvidenceKind
    url: str | None = None
    fetched_at: datetime | None = None
    knowledge_chunk_id: uuid.UUID | None = None
    section: ChunkSection | None = None
    place_fact_id: uuid.UUID | None = None
    publisher: str
    title: str | None = None
    locator: str | None = None
    verified_at: date | None


class GuideMessage(BaseModel):
    id: uuid.UUID
    seq: int = Field(ge=1)
    role: MessageRole
    input_mode: Literal["TEXT", "VOICE_TRANSCRIPT", "PHOTO"] | None = None
    content: str
    answer_status: AnswerStatus | None = None
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime


class GuideMessagePage(BaseModel):
    next_cursor: str | None = Field(description="Null on the last page.")
    items: list[GuideMessage]


class GuideStreamEvent(BaseModel):
    """One SSE ``data:`` payload; ``event:`` equals ``type``. ``result`` and ``error`` are
    terminal."""

    type: Literal["progress", "text", "result", "error"]
    stage: GuideStage | None = None
    delta: str | None = None
    message: GuideMessage | None = None
    error: ErrorDetail | None = None

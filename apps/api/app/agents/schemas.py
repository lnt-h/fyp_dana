"""Pydantic contracts of the three Agno roles (architecture §3.1).

Output schemas are what a model must return; every result is re-validated here with
``extra="forbid"`` (Groq is JSON mode only, Gemini output is re-checked too) and then by the
domain validators in :mod:`app.agents.validators`. Identifiers are plain strings on the wire
(Gemini structured output rejects ``format: uuid``); validators map them back to catalog IDs.

This module imports only the standard library and Pydantic so that ``app.research`` and the
orchestrators can depend on it without pulling in Agno.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Annotated, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Locale = Literal["vi", "en"]

MAX_PICKS = 24
MAX_UNMET = 3
MAX_RESEARCH_CANDIDATES = 5
MAX_RESEARCH_EVIDENCE = 4
MAX_FACTS_PER_CANDIDATE = 6
MAX_CLAIMS = 8

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Quote = Annotated[str, StringConstraints(strip_whitespace=True, min_length=4, max_length=400)]
UrlText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=8, max_length=2000)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ---------------------------------------------------------------------------------------------
# selector
# ---------------------------------------------------------------------------------------------


class Pick(_Strict):
    place_id: str = Field(description="Exactly one place_id copied from the candidate list.")
    rank: int = Field(ge=1, le=MAX_PICKS, description="1 = best match.")
    day_hint: int | None = Field(default=None, ge=1, le=3, description="Preferred trip day.")


class SelectionResult(_Strict):
    picks: list[Pick] = Field(max_length=MAX_PICKS)
    unmet_requests: list[ShortText] = Field(default_factory=list, max_length=MAX_UNMET)


# ---------------------------------------------------------------------------------------------
# grounded_writer
# ---------------------------------------------------------------------------------------------


class Rationale(_Strict):
    place_id: str
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=280)]


class RationaleSet(_Strict):
    rationales: list[Rationale] = Field(max_length=MAX_PICKS)


class AnswerStatus(StrEnum):
    ANSWERED = "ANSWERED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Claim(_Strict):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=600)]
    evidence_ids: list[ShortText] = Field(min_length=1, max_length=4)


class GroundedAnswer(_Strict):
    status: AnswerStatus
    claims: list[Claim] = Field(default_factory=list, max_length=MAX_CLAIMS)


# ---------------------------------------------------------------------------------------------
# researcher
# ---------------------------------------------------------------------------------------------

# Subset of the fact_fields vocabulary (cli FACT_FIELDS) a web page may *claim*. Claims are
# stored only in web_place_candidates.extraction, never in place_facts (architecture §4).
FactCode = Literal[
    "OPENING_HOURS",
    "ADMISSION_PRICE",
    "ADDRESS_VI",
    "PAYMENT_METHODS",
    "DRESS_CODE",
    "ACCESS_RULES",
]

CategoryGuess = Literal[
    "HERITAGE",
    "MUSEUM",
    "RELIGIOUS_SITE",
    "BEACH",
    "NATURE",
    "VIEWPOINT",
    "MARKET",
    "FOOD",
    "CAFE",
    "NIGHTLIFE",
    "THEME_PARK",
    "CRAFT_VILLAGE",
]


class ExtractedFact(_Strict):
    field: FactCode
    value: ShortText
    quote: Quote = Field(description="Verbatim sentence copied from the fetched page text.")


class WebCandidate(_Strict):
    name: ShortText
    name_vi: ShortText | None = None
    name_en: ShortText | None = None
    category_guess: CategoryGuess | None = None
    source_url: UrlText = Field(description="URL of a page returned by fetch_page.")
    google_place_id: ShortText | None = Field(
        default=None, description="place_id returned by places_check, if any."
    )
    name_quote: Quote = Field(description="Verbatim text from the page that names the place.")
    facts: list[ExtractedFact] = Field(default_factory=list, max_length=MAX_FACTS_PER_CANDIDATE)


class WebEvidence(_Strict):
    source_url: UrlText
    quote: Quote
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None = None


class ResearchReport(_Strict):
    candidates: list[WebCandidate] = Field(default_factory=list, max_length=MAX_RESEARCH_CANDIDATES)
    evidence: list[WebEvidence] = Field(default_factory=list, max_length=MAX_RESEARCH_EVIDENCE)


# ---------------------------------------------------------------------------------------------
# Inputs supplied by the orchestrator (already provider-safe; no coordinates, no contact data)
# ---------------------------------------------------------------------------------------------


class EvidenceItem(_Strict):
    """One unit of evidence the writer may cite (an approved fact, chunk or web quote)."""

    evidence_id: ShortText
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    label: ShortText | None = None  # e.g. place name or source host, shown to the model only


class RationaleStop(_Strict):
    place_id: uuid.UUID
    name: ShortText
    category_code: ShortText
    summary: str | None = Field(default=None, max_length=600)
    tags: list[ShortText] = Field(default_factory=list, max_length=12)


# ---------------------------------------------------------------------------------------------
# Research tools contract (implemented by app.research.toolbox; injected into the agent)
# ---------------------------------------------------------------------------------------------


@runtime_checkable
class ResearchTools(Protocol):
    """Tool surface of the researcher. Implementations enforce the per-run caps, redaction and
    caching; each method returns the text the model sees (never raises for a cap or a
    provider error, it returns an explanatory string instead)."""

    async def tavily_search(self, query: str) -> str: ...

    async def fetch_page(self, url: str) -> str: ...

    async def places_check(self, name: str) -> str: ...

    def page_text(self, url: str) -> str | None:
        """Text of a page fetched in this run exactly as shown to the model, or None."""
        ...

    def search_urls(self) -> frozenset[str]:
        """Normalised URLs returned by searches in this run."""
        ...

    def places_result(self, google_place_id: str) -> str | None:
        """Outcome recorded for a ``place_id`` returned by places_check in this run."""
        ...


# ---------------------------------------------------------------------------------------------
# Run outcomes (returned to the orchestrator; metadata only)
# ---------------------------------------------------------------------------------------------


class ResultSource(StrEnum):
    MODEL = "MODEL"
    REPAIRED = "REPAIRED"
    RULE_BASED = "RULE_BASED"
    DEGRADED = "DEGRADED"  # chain exhausted or quota: null rationales / skipped research


@dataclass(frozen=True, slots=True)
class Attempt:
    """One model call. No prompt, output or provider text is kept."""

    provider_model: str
    outcome: str  # app.ai.invocations.Outcome value
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    error_code: str | None = None
    tool_calls: int = 0


@dataclass(frozen=True, slots=True)
class SelectionOutcome:
    result: SelectionResult
    source: ResultSource
    attempts: Sequence[Attempt] = ()
    issues: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class RationaleOutcome:
    rationales: dict[uuid.UUID, str | None]
    source: ResultSource
    attempts: Sequence[Attempt] = ()
    issues: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class GuideAnswerOutcome:
    answer: GroundedAnswer
    source: ResultSource
    attempts: Sequence[Attempt] = ()
    dropped_claims: int = 0
    issues: Sequence[str] = ()


@dataclass(frozen=True, slots=True)
class ResearchOutcome:
    report: ResearchReport
    source: ResultSource
    attempts: Sequence[Attempt] = ()
    dropped: Sequence[str] = field(default_factory=tuple)

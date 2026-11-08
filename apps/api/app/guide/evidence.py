"""Evidence records shared by the Guide store, the retriever and the service.

An :class:`Evidence` is one approved fact pinned by a current publication or one approved chunk of
the pinned corpus revision, with the source revision a citation will point to. Facts and chunks
stay separate (ADR-010: facts never live in chunks).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

EvidenceKind = Literal["FACT", "CHUNK"]

# Fact fields the Guide may quote. ENTRANCE_LOCATION (coordinates) is not useful as prose.
FACT_LABELS: dict[str, str] = {
    "OPENING_HOURS": "Opening hours",
    "ADMISSION_PRICE": "Admission price",
    "ADDRESS_VI": "Address",
    "PAYMENT_METHODS": "Payment methods",
    "DRESS_CODE": "Dress code",
    "ACCESS_RULES": "Access rules",
}
CHUNK_SECTIONS = frozenset(
    {"OVERVIEW", "HISTORY", "HIGHLIGHTS", "VISIT_TIPS", "ETIQUETTE", "ACCESS"}
)
MAX_EVIDENCE_CHARS = 2000


@dataclass(frozen=True, slots=True)
class PlaceName:
    place_id: uuid.UUID
    names: tuple[str, ...]  # VI name, EN name and approved aliases, as stored
    display_vi: str
    display_en: str

    def display(self, locale: str) -> str:
        return self.display_en if locale == "en" else self.display_vi


@dataclass(frozen=True, slots=True)
class Evidence:
    key: str  # "fact:<uuid>" | "chunk:<uuid>"
    kind: EvidenceKind
    place_id: uuid.UUID | None
    text: str
    source_revision_id: uuid.UUID
    publisher: str
    title: str | None
    locator: str | None
    verified_at: date | None
    knowledge_chunk_id: uuid.UUID | None = None
    place_fact_id: uuid.UUID | None = None
    section: str | None = None
    locale: str | None = None
    field_code: str | None = None
    label: str | None = None  # place name shown to the model


def fact_text(field_code: str, value: dict[str, Any], *, is_stale: bool) -> str:
    """Fact as one line of evidence text. The value is quoted as stored, never interpreted."""
    label = FACT_LABELS.get(field_code, field_code.replace("_", " ").capitalize())
    rendered = value.get("text") if isinstance(value.get("text"), str) else None
    body = rendered or json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    note = " (verified long ago; may be outdated)" if is_stale else ""
    return f"{label}: {body}{note}"[:MAX_EVIDENCE_CHARS]


def citation_section(section: str | None) -> str | None:
    """Contract sections only; CITY-scope sections (CITY_OVERVIEW, ...) cite with null."""
    return section if section in CHUNK_SECTIONS else None

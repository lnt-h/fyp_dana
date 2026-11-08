"""Guide retrieval (ADR-010, DEC-017).

* **PLACE scope (Tier 1):** every approved fact pinned by the place's current publication and every
  approved chunk of its pinned corpus revision for the session locale (other locale as fallback).
  No question embedding, no threshold.
* **CITY scope (hybrid):** entity match on published place names and aliases (VI/EN, diacritic
  folded) → lexical match on approved chunks (``ILIKE`` over the trigram index) → vector
  similarity over chunk embeddings when any exist for the query embedding model (ADR-010 0.5
  model-consistency rule). The ranked lists are merged by reciprocal rank fusion.

Everything here is deterministic code; no model chooses evidence. Questions are never logged.
"""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from app.catalog.normalize import fold_words
from app.guide.evidence import Evidence, PlaceName

logger = logging.getLogger("gonarra.guide")

RRF_K = 60
MAX_ENTITY_PLACES = 3
MAX_LEXICAL = 12
MAX_VECTOR = 8
MAX_PATTERNS = 12
MAX_FUSED = 16
# Cosine distance cut for city-scoped vector hits. Uncalibrated (OQ-032): loose on purpose, the
# grounded writer still refuses when the evidence does not answer the question.
VECTOR_MAX_DISTANCE = 0.6
MIN_ENTITY_CHARS = 4

_TOKEN = re.compile(r"\w+", re.UNICODE)
# Function words that would match almost every chunk (lower-case, as typed).
# fmt: off
STOPWORDS = frozenset(
    {
        # en
        "the", "and", "for", "are", "was", "what", "when", "where", "which", "who", "how", "why",
        "does", "did", "can", "could", "should", "would", "there", "this", "that", "with",
        "from", "about", "into", "have", "has", "you", "your", "any", "some", "tell", "me",
        "is", "it", "of", "to", "in", "on", "at", "a", "an", "do", "be", "or", "i", "we",
        # vi
        "và", "là", "của", "có", "không", "cho", "với", "được", "những", "các", "một", "này",
        "đó", "thì", "mà", "ở", "tại", "nào", "gì", "sao", "bao", "nhiêu", "như", "thế", "hãy",
        "tôi", "mình", "bạn", "em", "anh", "chị", "nên", "đi", "đến", "vào", "ra", "khi",
    }
)
# fmt: on
# Folded keywords → fact fields, used to rank an entity's facts (not to filter them).
FACT_INTENTS: dict[str, tuple[str, ...]] = {
    "OPENING_HOURS": ("hour", "open", "close", "closing", "time", "gio", "mo cua", "dong cua"),
    "ADMISSION_PRICE": (
        "price",
        "ticket",
        "fee",
        "cost",
        "admission",
        "gia",
        "gia ve",
        "mua ve",
        "phi",
    ),
    "ADDRESS_VI": ("address", "where", "located", "dia chi", "o dau", "nam o"),
    "PAYMENT_METHODS": ("pay", "card", "cash", "payment", "thanh toan", "the tin dung", "tien mat"),
    "DRESS_CODE": ("dress", "wear", "clothes", "trang phuc", "mac", "quan ao"),
    "ACCESS_RULES": ("rule", "allowed", "permit", "access", "quy dinh", "duoc phep"),
}


@dataclass(frozen=True, slots=True)
class QueryVector:
    vector: list[float]
    model: str


class QueryEmbedder(Protocol):
    async def embed(self, question: str, *, account_id: uuid.UUID) -> QueryVector | None: ...


class EvidenceSource(Protocol):
    """Read-only catalog queries the retriever needs (published content only)."""

    async def place_names(self, city_id: uuid.UUID) -> list[PlaceName]: ...

    async def place_evidence(
        self, place_ids: Sequence[uuid.UUID], locales: Sequence[str]
    ) -> list[Evidence]: ...

    async def lexical_chunks(
        self, city_id: uuid.UUID, patterns: Sequence[str], locales: Sequence[str], limit: int
    ) -> list[Evidence]: ...

    async def embedding_models(self, city_id: uuid.UUID) -> set[str]: ...

    async def vector_chunks(
        self,
        city_id: uuid.UUID,
        vector: Sequence[float],
        model: str,
        locales: Sequence[str],
        limit: int,
        max_distance: float,
    ) -> list[Evidence]: ...


@dataclass(slots=True)
class RetrievalResult:
    evidence: list[Evidence]
    channels: dict[str, int] = field(default_factory=dict)  # counts only, for logs


# ---- pure helpers -------------------------------------------------------------------------------


def other_locale(locale: str) -> str:
    return "vi" if locale == "en" else "en"


def match_entities(question: str, places: Sequence[PlaceName]) -> list[uuid.UUID]:
    """Published places whose folded name or alias occurs as whole words in the question.

    Longer matches rank first ("Chùa Linh Ứng Bãi Bụt" before "Linh Ứng").
    """
    folded = f" {fold_words(question)} "
    scored: dict[uuid.UUID, int] = {}
    for place in places:
        for name in place.names:
            needle = fold_words(name)
            if len(needle) < MIN_ENTITY_CHARS:
                continue
            if f" {needle} " in folded:
                scored[place.place_id] = max(scored.get(place.place_id, 0), len(needle))
    ranked = sorted(scored.items(), key=lambda item: (-item[1], str(item[0])))
    return [place_id for place_id, _ in ranked[:MAX_ENTITY_PLACES]]


def lexical_patterns(question: str) -> list[str]:
    """``ILIKE`` patterns from the question as typed (diacritics kept, lower-case): content words
    of ≥ 3 characters, plus adjacent word pairs so that Vietnamese two-syllable words
    ("mở cửa", "bãi biển") match as phrases."""
    words = [w for w in _TOKEN.findall(question.lower()) if not w.isdigit()]
    content = [w for w in words if w not in STOPWORDS]
    terms: list[str] = []
    for first, second in zip(words, words[1:], strict=False):
        if first in STOPWORDS and second in STOPWORDS:
            continue
        terms.append(f"{first} {second}")
    terms.extend(w for w in content if len(w) >= 3)
    seen: list[str] = []
    for term in terms:
        escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        if pattern not in seen:
            seen.append(pattern)
    return seen[:MAX_PATTERNS]


def fact_intents(question: str) -> set[str]:
    folded = f" {fold_words(question)} "
    return {
        code
        for code, keywords in FACT_INTENTS.items()
        if any(f" {keyword}" in folded for keyword in keywords)
    }


def reciprocal_rank_fusion(rankings: Sequence[Sequence[str]], *, k: int = RRF_K) -> list[str]:
    """Merge ranked key lists: score = Σ 1 / (k + rank). Ties keep first-seen order."""
    scores: dict[str, float] = {}
    order: dict[str, int] = {}
    for ranking in rankings:
        for rank, key in enumerate(ranking, start=1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            order.setdefault(key, len(order))
    return sorted(scores, key=lambda key: (-scores[key], order[key]))


def rank_place_evidence(
    evidence: Sequence[Evidence],
    *,
    entity_order: Sequence[uuid.UUID],
    locale: str,
    intents: set[str],
) -> list[Evidence]:
    """Entity channel order: per matched place, facts the question asks about, then chunks in the
    session locale, then the remaining facts, then other-locale chunks."""
    position = {place_id: index for index, place_id in enumerate(entity_order)}

    def key(item: Evidence) -> tuple[int, int, str]:
        if item.kind == "FACT":
            tier = 0 if item.field_code in intents else 2
        else:
            tier = 1 if item.locale == locale else 3
        return (position.get(item.place_id, len(position)) if item.place_id else 0, tier, item.key)

    return sorted(evidence, key=key)


def place_scope_evidence(evidence: Sequence[Evidence], locale: str) -> list[Evidence]:
    """Tier 1: all facts + chunks in the session locale; other-locale chunks only when the
    session locale has none (answered in the session locale)."""
    facts = [item for item in evidence if item.kind == "FACT"]
    chunks = [item for item in evidence if item.kind == "CHUNK" and item.locale == locale]
    if not chunks:
        chunks = [item for item in evidence if item.kind == "CHUNK"]
    return [*chunks, *facts]


# ---- retriever ----------------------------------------------------------------------------------


class HybridRetriever:
    def __init__(self, embedder: QueryEmbedder | None = None) -> None:
        self._embedder = embedder

    async def for_place(
        self, source: EvidenceSource, place_id: uuid.UUID, locale: str
    ) -> RetrievalResult:
        evidence = await source.place_evidence([place_id], [locale, other_locale(locale)])
        selected = place_scope_evidence(evidence, locale)
        return RetrievalResult(selected, {"place": len(selected)})

    async def for_city(
        self,
        source: EvidenceSource,
        *,
        city_id: uuid.UUID,
        question: str,
        locale: str,
        account_id: uuid.UUID,
    ) -> RetrievalResult:
        locales = [locale, other_locale(locale)]
        by_key: dict[str, Evidence] = {}
        rankings: list[list[str]] = []
        channels: dict[str, int] = {}

        # 1. entity
        entities = match_entities(question, await source.place_names(city_id))
        if entities:
            ranked = rank_place_evidence(
                await source.place_evidence(entities, locales),
                entity_order=entities,
                locale=locale,
                intents=fact_intents(question),
            )
            rankings.append(self._remember(ranked, by_key))
        channels["entity"] = len(rankings[0]) if rankings else 0

        # 2. lexical
        patterns = lexical_patterns(question)
        lexical = (
            await source.lexical_chunks(city_id, patterns, locales, MAX_LEXICAL) if patterns else []
        )
        if lexical:
            rankings.append(self._remember(lexical, by_key))
        channels["lexical"] = len(lexical)

        # 3. vector (only over chunks embedded with the query model)
        vector_hits = await self._vector(source, city_id, question, locales, account_id)
        if vector_hits:
            rankings.append(self._remember(vector_hits, by_key))
        channels["vector"] = len(vector_hits)

        fused = reciprocal_rank_fusion(rankings)[:MAX_FUSED]
        return RetrievalResult([by_key[key] for key in fused], channels)

    async def _vector(
        self,
        source: EvidenceSource,
        city_id: uuid.UUID,
        question: str,
        locales: Sequence[str],
        account_id: uuid.UUID,
    ) -> list[Evidence]:
        models = await source.embedding_models(city_id)
        if not models:
            logger.info("guide retrieval vector=skipped reason=no_embeddings")
            return []
        if self._embedder is None:
            logger.info("guide retrieval vector=skipped reason=no_embedder")
            return []
        query = await self._embedder.embed(question, account_id=account_id)
        if query is None:
            logger.info("guide retrieval vector=skipped reason=embed_unavailable")
            return []
        if query.model not in models:
            logger.warning("guide retrieval vector=skipped reason=model_mismatch")
            return []
        return await source.vector_chunks(
            city_id, query.vector, query.model, locales, MAX_VECTOR, VECTOR_MAX_DISTANCE
        )

    @staticmethod
    def _remember(items: Sequence[Evidence], by_key: dict[str, Evidence]) -> list[str]:
        keys: list[str] = []
        for item in items:
            by_key.setdefault(item.key, item)
            if item.key not in keys:
                keys.append(item.key)
        return keys

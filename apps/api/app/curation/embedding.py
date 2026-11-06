"""Chunk embedding on write (ADR-012 0.4, OQ-126).

``embed`` returns an L2-normalised 768-dim vector or ``None``. ``None`` never fails the save:
the chunk is stored with ``embedding`` NULL (``embedding_state`` PENDING) and the CLI backfill
(``embed --pending``) finds it with ``embedding IS NULL AND review_state <> 'RETIRED'``.
Every attempted call goes through the quota ledger (bucket GEMINI_EMBED) and records an
``ai_invocations`` row (purpose CORPUS_EMBED, no account, no text).
"""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from app.ai.invocations import Outcome, Purpose, record_invocation, timed
from app.ai.providers import (
    EMBEDDING_DIMENSIONS,
    GEMINI_EMBEDDING,
    Provider,
    Role,
    make_embedder,
    provider_configured,
)
from app.ai.quota import Bucket, QuotaLedger, SessionFactory
from app.config import Settings

logger = logging.getLogger("gonarra.curation")

EMBED_TIMEOUT_S = 15.0


@dataclass(frozen=True, slots=True)
class Embedding:
    vector: list[float]
    model: str


class ChunkEmbedder(Protocol):
    async def embed(self, text: str) -> Embedding | None: ...


class DisabledEmbedder:
    """Embedder used when no provider is wired (tests, offline): always PENDING."""

    async def embed(self, text: str) -> Embedding | None:
        return None


def l2_normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0 or not math.isfinite(norm):
        raise ValueError("cannot normalise a zero or non-finite vector")
    return [value / norm for value in vector]


EmbedCall = Callable[[str], Awaitable[Sequence[float]]]


class GeminiChunkEmbedder:
    """``gemini-embedding-001`` (RETRIEVAL_DOCUMENT, 768 dims) behind the quota ledger."""

    def __init__(
        self,
        settings: Settings,
        session_factory: SessionFactory,
        *,
        ledger: QuotaLedger | None = None,
        call: EmbedCall | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._ledger = ledger or QuotaLedger(session_factory, settings)
        self._call = call

    async def _invoke(self, text: str) -> Sequence[float]:
        if self._call is not None:
            return await self._call(text)
        embedder = make_embedder(self._settings, task_type="RETRIEVAL_DOCUMENT")
        return await embedder.async_get_embedding(text)

    async def _record(self, outcome: Outcome, latency_ms: int) -> None:
        await record_invocation(
            self._session_factory,
            purpose=Purpose.CORPUS_EMBED,
            role=Role.EMBEDDING,
            provider=Provider.GEMINI,
            model_id=GEMINI_EMBEDDING,
            outcome=outcome,
            latency_ms=latency_ms,
        )

    async def embed(self, text: str) -> Embedding | None:
        if self._call is None and not provider_configured(Provider.GEMINI, self._settings):
            logger.info("chunk embedding pending reason=not_configured")
            return None
        decision = await self._ledger.reserve(bucket=Bucket.GEMINI_EMBED)
        if decision.reservation is None:
            await self._record(Outcome.QUOTA_EXCEEDED, 0)
            logger.info("chunk embedding pending reason=quota")
            return None
        reservation = decision.reservation
        outcome = Outcome.OK
        vector: list[float] | None = None
        with timed() as timer:
            try:
                raw = await asyncio.wait_for(self._invoke(text), timeout=EMBED_TIMEOUT_S)
                if len(raw) != EMBEDDING_DIMENSIONS:
                    outcome = Outcome.VALIDATION_FAILED
                else:
                    vector = l2_normalize([float(value) for value in raw])
            except TimeoutError:
                outcome = Outcome.TIMEOUT
            except ValueError:
                outcome = Outcome.VALIDATION_FAILED
            except Exception:  # noqa: BLE001 - any provider failure degrades to PENDING
                outcome = Outcome.PROVIDER_ERROR
        await self._ledger.commit(reservation)
        await self._record(outcome, timer.elapsed_ms)
        if vector is None:
            logger.info("chunk embedding pending reason=%s", outcome.value)
            return None
        return Embedding(vector=vector, model=GEMINI_EMBEDDING)

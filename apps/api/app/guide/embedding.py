"""Question embedding for city-scoped vector retrieval (ADR-010 0.5, purpose QUERY_EMBED).

The question is redacted (BR-046) and checked fail-closed before it leaves the server; the call
goes through the quota ledger (bucket GEMINI_EMBED) and records an ``ai_invocations`` row with the
asking account (metadata only, never the text). Any failure returns ``None`` and the retriever
continues with entity + lexical evidence.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable, Sequence

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
from app.ai.redaction import RedactionError, ensure_clean, redact_text
from app.config import Settings
from app.guide.retrieval import QueryVector

logger = logging.getLogger("gonarra.guide")

EMBED_TIMEOUT_S = 10.0
MAX_QUERY_CHARS = 2000

EmbedCall = Callable[[str], Awaitable[Sequence[float]]]


def _normalize(vector: Sequence[float]) -> list[float]:
    norm = sum(value * value for value in vector) ** 0.5
    if norm == 0.0:
        raise ValueError("zero vector")
    return [value / norm for value in vector]


class GeminiQueryEmbedder:
    """``gemini-embedding-001`` (RETRIEVAL_QUERY, 768 dims) behind the quota ledger."""

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
        embedder = make_embedder(self._settings, task_type="RETRIEVAL_QUERY")
        return await embedder.async_get_embedding(text)

    async def embed(self, question: str, *, account_id: uuid.UUID) -> QueryVector | None:
        if self._call is None and not provider_configured(Provider.GEMINI, self._settings):
            return None
        try:
            text = ensure_clean(redact_text(question)[:MAX_QUERY_CHARS])
        except RedactionError:
            logger.warning("guide query embedding refused reason=redaction")
            return None
        decision = await self._ledger.reserve(bucket=Bucket.GEMINI_EMBED)
        if decision.reservation is None:
            await self._record(Outcome.QUOTA_EXCEEDED, 0, account_id)
            return None
        outcome = Outcome.OK
        vector: list[float] | None = None
        with timed() as timer:
            try:
                raw = await asyncio.wait_for(self._invoke(text), timeout=EMBED_TIMEOUT_S)
                if len(raw) != EMBEDDING_DIMENSIONS:
                    outcome = Outcome.VALIDATION_FAILED
                else:
                    vector = _normalize([float(value) for value in raw])
            except TimeoutError:
                outcome = Outcome.TIMEOUT
            except ValueError:
                outcome = Outcome.VALIDATION_FAILED
            except Exception:  # noqa: BLE001 - any provider failure degrades to no vector
                outcome = Outcome.PROVIDER_ERROR
        await self._ledger.commit(decision.reservation)
        await self._record(outcome, timer.elapsed_ms, account_id)
        if vector is None:
            return None
        return QueryVector(vector=vector, model=GEMINI_EMBEDDING)

    async def _record(self, outcome: Outcome, latency_ms: int, account_id: uuid.UUID) -> None:
        await record_invocation(
            self._session_factory,
            purpose=Purpose.QUERY_EMBED,
            role=Role.EMBEDDING,
            provider=Provider.GEMINI,
            model_id=GEMINI_EMBEDDING,
            outcome=outcome,
            latency_ms=latency_ms,
            account_id=account_id,
        )

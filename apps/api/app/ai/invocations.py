"""``ai_invocations`` writer: safe AI usage metadata only (architecture §6, schema.sql §7).

Stored: purpose, provider/model, prompt version, corpus revision, outcome, latency, token
counts and the owning account. Never stored or logged: prompts, questions, answers,
transcripts, tool arguments or provider bodies.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.ai.providers import Provider, Role
from app.ai.quota import SessionFactory

logger = logging.getLogger("gonarra.ai")


class Purpose(StrEnum):
    """Mirrors ``ck_ai_invocations_purpose``."""

    PLAN_GENERATE = "PLAN_GENERATE"
    PLAN_REPAIR = "PLAN_REPAIR"
    DAY_REGENERATE = "DAY_REGENERATE"
    GUIDE_ANSWER = "GUIDE_ANSWER"
    PHOTO_IDENTIFY = "PHOTO_IDENTIFY"
    CORPUS_EMBED = "CORPUS_EMBED"
    QUERY_EMBED = "QUERY_EMBED"
    TRANSLATION_DRAFT = "TRANSLATION_DRAFT"
    # Migration 0007: offline grounded place descriptions (``enrich descriptions``).
    CONTENT_SUMMARY = "CONTENT_SUMMARY"


class Outcome(StrEnum):
    """Mirrors ``ck_ai_invocations_outcome``."""

    OK = "OK"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    TIMEOUT = "TIMEOUT"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"
    REFUSED_BY_CAP = "REFUSED_BY_CAP"


# ck_ai_invocations_traveler_purpose: only these purposes may have no account.
ACCOUNTLESS_PURPOSES = frozenset(
    {Purpose.CORPUS_EMBED, Purpose.TRANSLATION_DRAFT, Purpose.CONTENT_SUMMARY}
)

_INSERT = text(
    "/* ai:invocation */ INSERT INTO ai_invocations "
    "(id, account_id, purpose, provider_model, prompt_version, corpus_revision, outcome, "
    "latency_ms, input_tokens, output_tokens) "
    "VALUES (:id, :account_id, :purpose, :provider_model, :prompt_version, :corpus_revision, "
    ":outcome, :latency_ms, :input_tokens, :output_tokens)"
)


def provider_model(provider: Provider, model_id: str) -> str:
    """Value stored in ``ai_invocations.provider_model``, e.g. ``GEMINI:gemini-2.5-flash``."""
    return f"{provider.value}:{model_id}"


async def record_invocation(
    session_factory: SessionFactory,
    *,
    purpose: Purpose,
    role: Role,
    provider: Provider,
    model_id: str,
    outcome: Outcome,
    latency_ms: int,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    account_id: uuid.UUID | None = None,
    agent_run_id: uuid.UUID | None = None,
    error_code: str | None = None,
    prompt_version: str | None = None,
    corpus_revision: int | None = None,
) -> uuid.UUID | None:
    """Insert one metadata row in its own short transaction; returns its id.

    ``role``, ``agent_run_id`` and ``error_code`` have no column in the current DDL and are
    only logged. A database failure is logged and returns ``None`` (telemetry never fails a
    request). Contract violations (missing account for a traveler purpose, negative numbers)
    raise ``ValueError`` because they are programming errors.
    """
    if account_id is None and purpose not in ACCOUNTLESS_PURPOSES:
        raise ValueError(f"{purpose.value} invocations require account_id")
    if latency_ms < 0 or any(n is not None and n < 0 for n in (input_tokens, output_tokens)):
        raise ValueError("latency and token counts must be non-negative")

    invocation_id = uuid.uuid4()
    params = {
        "id": invocation_id,
        "account_id": account_id,
        "purpose": purpose.value,
        "provider_model": provider_model(provider, model_id),
        "prompt_version": prompt_version,
        "corpus_revision": corpus_revision,
        "outcome": outcome.value,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    try:
        async with session_factory() as session:
            await session.execute(_INSERT, params)
            await session.commit()
    except SQLAlchemyError:
        logger.warning(
            "invocation not recorded role=%s model=%s outcome=%s",
            role.value,
            model_id,
            outcome.value,
        )
        return None
    logger.info(
        "invocation role=%s model=%s outcome=%s latency_ms=%d error=%s run=%s",
        role.value,
        model_id,
        outcome.value,
        latency_ms,
        error_code or "-",
        agent_run_id or "-",
    )
    return invocation_id


@dataclass
class Timer:
    started: float = field(default_factory=time.perf_counter)
    stopped: float | None = None

    @property
    def elapsed_ms(self) -> int:
        end = self.stopped if self.stopped is not None else time.perf_counter()
        return max(0, round((end - self.started) * 1000))


@contextmanager
def timed() -> Iterator[Timer]:
    """``with timed() as t: ...`` then ``t.elapsed_ms`` (frozen on exit, also on error)."""
    timer = Timer()
    try:
        yield timer
    finally:
        timer.stopped = time.perf_counter()

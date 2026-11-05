import logging
import time
import uuid
from typing import Any

import pytest

from app.ai.invocations import Outcome, Purpose, record_invocation, timed
from app.ai.providers import Provider, Role

ACCOUNT = uuid.UUID("11111111-1111-4111-8111-111111111111")
DDL_COLUMNS = {
    "id",
    "account_id",
    "purpose",
    "provider_model",
    "prompt_version",
    "corpus_revision",
    "outcome",
    "latency_ms",
    "input_tokens",
    "output_tokens",
}


async def test_record_invocation_shape(db: Any, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="gonarra.ai")
    run_id = uuid.uuid4()
    invocation_id = await record_invocation(
        db.factory(),
        purpose=Purpose.PLAN_GENERATE,
        role=Role.SELECTOR,
        provider=Provider.GEMINI,
        model_id="gemini-2.5-flash",
        outcome=Outcome.VALIDATION_FAILED,
        latency_ms=812,
        input_tokens=1500,
        output_tokens=300,
        account_id=ACCOUNT,
        agent_run_id=run_id,
        error_code="UNKNOWN_PLACE_ID",
        prompt_version="selector.v1",
    )
    (row,) = db.invocations
    assert set(row) == DDL_COLUMNS
    assert row["id"] == invocation_id
    assert row["provider_model"] == "GEMINI:gemini-2.5-flash"
    assert row["purpose"] == "PLAN_GENERATE" and row["outcome"] == "VALIDATION_FAILED"
    assert row["account_id"] == ACCOUNT and row["corpus_revision"] is None
    assert db.commits == 1
    assert "role=SELECTOR" in caplog.text and "error=UNKNOWN_PLACE_ID" in caplog.text
    assert str(ACCOUNT) not in caplog.text


async def test_traveler_purpose_requires_account(db: Any) -> None:
    with pytest.raises(ValueError):
        await record_invocation(
            db.factory(),
            purpose=Purpose.GUIDE_ANSWER,
            role=Role.WRITER_GUIDE,
            provider=Provider.GROQ,
            model_id="llama-3.3-70b-versatile",
            outcome=Outcome.OK,
            latency_ms=10,
        )
    assert (
        await record_invocation(
            db.factory(),
            purpose=Purpose.CORPUS_EMBED,
            role=Role.EMBEDDING,
            provider=Provider.GEMINI,
            model_id="gemini-embedding-001",
            outcome=Outcome.OK,
            latency_ms=10,
        )
        is not None
    )


async def test_database_failure_is_swallowed(db: Any) -> None:
    db.fail = True
    result = await record_invocation(
        db.factory(),
        purpose=Purpose.QUERY_EMBED,
        role=Role.EMBEDDING,
        provider=Provider.GEMINI,
        model_id="gemini-embedding-001",
        outcome=Outcome.TIMEOUT,
        latency_ms=15000,
        account_id=ACCOUNT,
    )
    assert result is None


def test_timed_freezes_on_exit() -> None:
    with timed() as timer:
        time.sleep(0.01)
    elapsed = timer.elapsed_ms
    assert elapsed >= 10
    time.sleep(0.01)
    assert timer.elapsed_ms == elapsed

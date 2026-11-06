"""Chunk embedding on write (app.curation.embedding) with the fake quota/invocation DB."""

import math
from collections.abc import Callable, Sequence
from typing import Any

import pytest
from conftest import FakeDb

from app.config import Settings
from app.curation.embedding import GeminiChunkEmbedder, l2_normalize


def _call(vector: Sequence[float]) -> Callable[[str], Any]:
    async def call(_: str) -> Sequence[float]:
        return vector

    return call


async def test_not_configured_is_pending_without_quota_or_invocation(
    db: FakeDb, settings_factory: Callable[..., Settings]
) -> None:
    settings = settings_factory(gemini_api_key=None)
    embedder = GeminiChunkEmbedder(settings, db.factory())
    assert await embedder.embed("Chùa Cầu") is None
    assert db.statements == []


async def test_success_is_normalised_and_accounted(db: FakeDb, settings: Settings) -> None:
    embedder = GeminiChunkEmbedder(settings, db.factory(), call=_call([3.0, 4.0] + [0.0] * 766))
    result = await embedder.embed("Chùa Cầu")
    assert result is not None
    assert result.model == "gemini-embedding-001"
    assert len(result.vector) == 768
    assert result.vector[:2] == pytest.approx([0.6, 0.8])
    assert math.isclose(math.sqrt(sum(v * v for v in result.vector)), 1.0)
    assert "quota:commit" in db.statements
    [invocation] = db.invocations
    assert invocation["purpose"] == "CORPUS_EMBED"
    assert invocation["outcome"] == "OK"
    assert invocation["account_id"] is None
    assert "Chùa" not in str(invocation)


async def test_wrong_dimension_and_provider_error_degrade(db: FakeDb, settings: Settings) -> None:
    short = GeminiChunkEmbedder(settings, db.factory(), call=_call([1.0] * 10))
    assert await short.embed("x") is None

    async def boom(_: str) -> Sequence[float]:
        raise RuntimeError("provider down")

    failing = GeminiChunkEmbedder(settings, db.factory(), call=boom)
    assert await failing.embed("x") is None
    assert [row["outcome"] for row in db.invocations] == ["VALIDATION_FAILED", "PROVIDER_ERROR"]


async def test_quota_exhausted_is_pending(
    db: FakeDb, settings_factory: Callable[..., Settings]
) -> None:
    settings = settings_factory(quota_gemini_embed_per_day=1)
    embedder = GeminiChunkEmbedder(settings, db.factory(), call=_call([1.0] * 768))
    assert await embedder.embed("first") is not None
    assert await embedder.embed("second") is None
    assert db.invocations[-1]["outcome"] == "QUOTA_EXCEEDED"


def test_l2_normalize_rejects_zero_vector() -> None:
    with pytest.raises(ValueError):
        l2_normalize([0.0, 0.0])

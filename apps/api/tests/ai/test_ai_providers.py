import logging
from collections.abc import Callable

import pytest
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.models.google import Gemini
from agno.models.groq import Groq

from app.ai.providers import (
    EMBEDDING_DIMENSIONS,
    Provider,
    ProviderNotConfigured,
    Role,
    make_embedder,
    make_model,
    provider_configured,
    role_chain,
)
from app.config import Settings

GEMINI_KEY = "gem-test-SECRET-123"
GROQ_KEY = "groq-test-SECRET-456"


def test_role_chains_follow_architecture() -> None:
    assert [(s.provider, s.model_id) for s in role_chain(Role.SELECTOR)] == [
        (Provider.GEMINI, "gemini-2.5-flash"),
        (Provider.GROQ, "llama-3.3-70b-versatile"),
    ]
    assert [s.provider for s in role_chain(Role.RESEARCHER)] == [Provider.GROQ]
    assert role_chain(Role.WRITER_RATIONALE)[0].model_id == "gemini-2.5-flash-lite"
    assert role_chain(Role.WRITER_GUIDE)[0].model_id == "gemini-2.5-flash"
    assert role_chain(Role.EMBEDDING)[0].model_id == "gemini-embedding-001"
    for role in Role:
        for spec in role_chain(role):
            assert spec.role is role
            # Groq is JSON mode only; Gemini uses native structured output.
            assert spec.json_mode is (spec.provider is Provider.GROQ)


def test_role_chain_returns_a_copy() -> None:
    role_chain(Role.SELECTOR).clear()
    assert len(role_chain(Role.SELECTOR)) == 2


def test_make_model_builds_agno_models(settings: Settings) -> None:
    gemini, groq = (make_model(spec, settings) for spec in role_chain(Role.SELECTOR))
    assert isinstance(gemini, Gemini) and gemini.id == "gemini-2.5-flash"
    assert gemini.api_key == GEMINI_KEY
    assert gemini.max_output_tokens == 2048
    assert isinstance(groq, Groq) and groq.id == "llama-3.3-70b-versatile"
    assert groq.api_key == GROQ_KEY


def test_make_model_without_key_raises(settings_factory: Callable[..., Settings]) -> None:
    settings = settings_factory(gemini_api_key=None)
    with pytest.raises(ProviderNotConfigured) as excinfo:
        make_model(role_chain(Role.SELECTOR)[0], settings)
    assert excinfo.value.provider is Provider.GEMINI
    # Groq still builds.
    assert isinstance(make_model(role_chain(Role.SELECTOR)[1], settings), Groq)


@pytest.mark.parametrize("blank", ["", "   "])
def test_empty_key_counts_as_not_configured(
    settings_factory: Callable[..., Settings], blank: str
) -> None:
    settings = settings_factory(groq_api_key=blank)
    assert settings.groq_api_key is None
    assert not provider_configured(Provider.GROQ, settings)
    with pytest.raises(ProviderNotConfigured):
        make_model(role_chain(Role.RESEARCHER)[0], settings)


def test_empty_env_lines_parse_as_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GONARRA_GEMINI_API_KEY", "")
    monkeypatch.setenv("GONARRA_CLERK_AUDIENCE", "")
    monkeypatch.setenv("GONARRA_CLERK_JWKS_URL", "")
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.gemini_api_key is None
    assert settings.clerk_audience is None
    assert settings.clerk_jwks_url is None


def test_embedder_is_pinned_to_768_dimensions(settings: Settings) -> None:
    embedder = make_embedder(settings)
    assert isinstance(embedder, GeminiEmbedder)
    assert embedder.id == "gemini-embedding-001"
    assert embedder.dimensions == EMBEDDING_DIMENSIONS == 768
    with pytest.raises(ValueError):
        make_model(role_chain(Role.EMBEDDING)[0], settings)


def test_api_key_never_in_repr_or_logs(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG, logger="gonarra.ai")
    built = [make_model(spec, settings) for spec in role_chain(Role.SELECTOR)]
    embedder = make_embedder(settings)
    texts = [caplog.text, repr(settings)]
    texts += [repr(spec) for role in Role for spec in role_chain(role)]
    texts += [repr(model) for model in built] + [repr(embedder)]
    for value in texts:
        assert GEMINI_KEY not in value
        assert GROQ_KEY not in value
    assert "model built role=SELECTOR model=gemini-2.5-flash" in caplog.text

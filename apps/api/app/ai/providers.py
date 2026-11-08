"""Model specs, role fallback chains and Agno model construction (architecture §3.1).

Only this module (and ``app.agents``) imports Agno. API keys are read from :class:`Settings` at
build time, passed to the Agno object through a ``repr=False`` field and never logged.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from agno.knowledge.embedder.google import GeminiEmbedder
from agno.models.google import Gemini
from agno.models.groq import Groq

if TYPE_CHECKING:
    from agno.models.base import Model

    from app.config import Settings

logger = logging.getLogger("gonarra.ai")

# Chat models (SPK-004 + live key probe 2026-11-08): the originally pinned ``gemini-2.5-flash``,
# ``gemini-2.5-flash-lite`` and Groq ``llama-3.3-70b-versatile`` answer 404 for new API keys.
# Probe latencies with a JSON responseSchema: gemini-3.5-flash-lite 1.0 s, gemini-3.6-flash 3.0 s;
# gemini-3.8-flash / 3.7-flash / flash-latest think by default (24-30 s) and are not used. Groq
# openai/gpt-oss-120b: tool calling 0.7 s. Constant names keep the quota buckets stable
# (GEMINI_FLASH / GEMINI_FLASH_LITE / GROQ).
GEMINI_FLASH = "gemini-3.6-flash"
GEMINI_FLASH_LITE = "gemini-3.5-flash-lite"
GEMINI_EMBEDDING = "gemini-embedding-001"
GROQ_GPT_OSS_120B = "openai/gpt-oss-120b"
GROQ_DEFAULT = GROQ_GPT_OSS_120B

# knowledge_chunks.embedding is vector(768), pinned to gemini-embedding-001 (OQ-126).
EMBEDDING_DIMENSIONS = 768


class Provider(StrEnum):
    GEMINI = "GEMINI"
    GROQ = "GROQ"


class Role(StrEnum):
    SELECTOR = "SELECTOR"
    RESEARCHER = "RESEARCHER"
    WRITER_RATIONALE = "WRITER_RATIONALE"
    WRITER_GUIDE = "WRITER_GUIDE"
    WRITER_DESCRIPTION = "WRITER_DESCRIPTION"  # offline grounded place descriptions (D3)
    EMBEDDING = "EMBEDDING"
    JUDGE = "JUDGE"


class ProviderNotConfigured(RuntimeError):
    """The provider's API key is missing from settings. Callers skip to the next chain entry."""

    def __init__(self, provider: Provider) -> None:
        super().__init__(f"{provider.value} API key is not configured")
        self.provider = provider


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """Static description of one model in a role chain. Holds no secrets."""

    provider: Provider
    model_id: str
    role: Role
    # Gemini: native structured output. Groq: JSON mode only, so the agent factory must set
    # ``use_json_mode=True`` and re-validate every result with the same Pydantic schema.
    json_mode: bool
    max_output_tokens: int | None
    timeout_s: float
    # Gemini 3 thinking level ("low" / "high"); ``None`` keeps the model default (the measured
    # configuration). SPK-004: thinking-by-default models hit 504 at ~28 s for 30 candidates.
    thinking_level: str | None = None


def _gemini(
    model_id: str,
    role: Role,
    *,
    max_tokens: int,
    timeout_s: float,
    thinking_level: str | None = None,
) -> ModelSpec:
    return ModelSpec(Provider.GEMINI, model_id, role, False, max_tokens, timeout_s, thinking_level)


def _groq(role: Role, *, max_tokens: int, timeout_s: float) -> ModelSpec:
    return ModelSpec(Provider.GROQ, GROQ_DEFAULT, role, True, max_tokens, timeout_s)


# Gemini 3 thinking tokens count against ``max_output_tokens``. With the default (dynamic)
# thinking, gemini-3.6-flash spent 1 073 of 2 048 tokens thinking on a 24-candidate selector
# prompt (7.8 s) and sometimes all but ~100, which cut the JSON mid-string ("Unterminated
# string", 2026-11-08). ``thinking_level="low"`` measured 0 thinking tokens and 3.4 s for the same
# prompt; Flash-Lite does not think by default. Budgets keep headroom over the largest output.
_FLASH_THINKING = "low"

# Timeouts are per provider request; the agent runtime adds 5 s for the whole Agno run. The
# planning chains are kept short so that a proposal with every model failing still finishes in
# well under a minute (then the rule-based selector / null rationales take over).
_CHAINS: dict[Role, tuple[ModelSpec, ...]] = {
    Role.SELECTOR: (
        # SelectionResult is IDs + ranks only: ~30 tokens per pick, ≤ 24 picks ≈ 750 tokens.
        _gemini(
            GEMINI_FLASH,
            Role.SELECTOR,
            max_tokens=4096,
            timeout_s=15.0,
            thinking_level=_FLASH_THINKING,
        ),
        _gemini(GEMINI_FLASH_LITE, Role.SELECTOR, max_tokens=4096, timeout_s=12.0),
        # gpt-oss always reasons and its reasoning counts against max_tokens as well.
        _groq(Role.SELECTOR, max_tokens=4096, timeout_s=15.0),
    ),
    # Researcher never runs on Gemini (ADR-014).
    Role.RESEARCHER: (_groq(Role.RESEARCHER, max_tokens=2048, timeout_s=30.0),),
    Role.WRITER_RATIONALE: (
        _gemini(GEMINI_FLASH_LITE, Role.WRITER_RATIONALE, max_tokens=2048, timeout_s=18.0),
        _groq(Role.WRITER_RATIONALE, max_tokens=2048, timeout_s=12.0),
    ),
    Role.WRITER_GUIDE: (
        _gemini(
            GEMINI_FLASH,
            Role.WRITER_GUIDE,
            max_tokens=1536,
            timeout_s=20.0,
            thinking_level=_FLASH_THINKING,
        ),
        _groq(Role.WRITER_GUIDE, max_tokens=1536, timeout_s=20.0),
    ),
    # Offline enrichment (no traveler waiting): longer timeouts, Flash-Lite first (free-tier RPD).
    Role.WRITER_DESCRIPTION: (
        _gemini(GEMINI_FLASH_LITE, Role.WRITER_DESCRIPTION, max_tokens=2048, timeout_s=30.0),
        _groq(Role.WRITER_DESCRIPTION, max_tokens=2048, timeout_s=30.0),
    ),
    Role.EMBEDDING: (
        ModelSpec(Provider.GEMINI, GEMINI_EMBEDDING, Role.EMBEDDING, False, None, 15.0),
    ),
    Role.JUDGE: (
        _gemini(
            GEMINI_FLASH,
            Role.JUDGE,
            max_tokens=1024,
            timeout_s=60.0,
            thinking_level=_FLASH_THINKING,
        ),
        _groq(Role.JUDGE, max_tokens=1024, timeout_s=60.0),
    ),
}


def role_chain(role: Role) -> list[ModelSpec]:
    """Ordered fallback chain for ``role`` (first entry preferred)."""
    return list(_CHAINS[role])


def provider_configured(provider: Provider, settings: Settings) -> bool:
    return _api_key(provider, settings, required=False) is not None


def _api_key(provider: Provider, settings: Settings, *, required: bool = True) -> str | None:
    secret = settings.gemini_api_key if provider is Provider.GEMINI else settings.groq_api_key
    value = secret.get_secret_value().strip() if secret is not None else ""
    if not value:
        if required:
            raise ProviderNotConfigured(provider)
        return None
    return value


# Agno's dataclass repr includes ``api_key``; these subclasses hide it so an accidental
# ``repr(model)`` in a log line or traceback never prints the secret.
@dataclass
class _SafeGemini(Gemini):
    api_key: str | None = field(default=None, repr=False)


@dataclass
class _SafeGroq(Groq):
    api_key: str | None = field(default=None, repr=False)


@dataclass
class _SafeGeminiEmbedder(GeminiEmbedder):
    api_key: str | None = field(default=None, repr=False)


def make_model(spec: ModelSpec, settings: Settings) -> Model:
    """Build the Agno chat model for ``spec``. Raises :class:`ProviderNotConfigured`."""
    if spec.role is Role.EMBEDDING:
        raise ValueError("use make_embedder() for the EMBEDDING role")
    key = _api_key(spec.provider, settings)
    model: Model
    if spec.provider is Provider.GEMINI:
        model = _SafeGemini(
            id=spec.model_id,
            api_key=key,
            max_output_tokens=spec.max_output_tokens,
            timeout=spec.timeout_s,
            thinking_level=spec.thinking_level,
        )
    else:
        model = _SafeGroq(
            id=spec.model_id,
            api_key=key,
            max_tokens=spec.max_output_tokens,
            timeout=int(spec.timeout_s),
        )
    logger.debug("model built role=%s model=%s", spec.role.value, spec.model_id)
    return model


def make_embedder(settings: Settings, *, task_type: str = "RETRIEVAL_QUERY") -> GeminiEmbedder:
    """Agno Gemini embedder pinned to ``gemini-embedding-001`` at 768 dimensions.

    ``task_type`` is ``RETRIEVAL_QUERY`` for questions and ``RETRIEVAL_DOCUMENT`` for chunks.
    Vectors must be L2-normalised by the caller before storage (OQ-126).
    """
    key = _api_key(Provider.GEMINI, settings)
    embedder = _SafeGeminiEmbedder(
        id=GEMINI_EMBEDDING,
        api_key=key,
        dimensions=EMBEDDING_DIMENSIONS,
        task_type=task_type,
    )
    logger.debug("embedder built model=%s", GEMINI_EMBEDDING)
    return embedder

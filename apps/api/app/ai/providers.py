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

GEMINI_FLASH = "gemini-2.5-flash"
GEMINI_FLASH_LITE = "gemini-2.5-flash-lite"
GEMINI_EMBEDDING = "gemini-embedding-001"
GROQ_LLAMA_70B = "llama-3.3-70b-versatile"

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


def _gemini(model_id: str, role: Role, *, max_tokens: int, timeout_s: float) -> ModelSpec:
    return ModelSpec(Provider.GEMINI, model_id, role, False, max_tokens, timeout_s)


def _groq(role: Role, *, max_tokens: int, timeout_s: float) -> ModelSpec:
    return ModelSpec(Provider.GROQ, GROQ_LLAMA_70B, role, True, max_tokens, timeout_s)


_CHAINS: dict[Role, tuple[ModelSpec, ...]] = {
    Role.SELECTOR: (
        _gemini(GEMINI_FLASH, Role.SELECTOR, max_tokens=2048, timeout_s=30.0),
        _groq(Role.SELECTOR, max_tokens=2048, timeout_s=30.0),
    ),
    # Researcher never runs on Gemini (ADR-014).
    Role.RESEARCHER: (_groq(Role.RESEARCHER, max_tokens=2048, timeout_s=45.0),),
    Role.WRITER_RATIONALE: (
        _gemini(GEMINI_FLASH_LITE, Role.WRITER_RATIONALE, max_tokens=2048, timeout_s=30.0),
        _groq(Role.WRITER_RATIONALE, max_tokens=2048, timeout_s=30.0),
    ),
    Role.WRITER_GUIDE: (
        _gemini(GEMINI_FLASH, Role.WRITER_GUIDE, max_tokens=1536, timeout_s=30.0),
        _groq(Role.WRITER_GUIDE, max_tokens=1536, timeout_s=30.0),
    ),
    Role.EMBEDDING: (
        ModelSpec(Provider.GEMINI, GEMINI_EMBEDDING, Role.EMBEDDING, False, None, 15.0),
    ),
    Role.JUDGE: (
        _gemini(GEMINI_FLASH, Role.JUDGE, max_tokens=1024, timeout_s=60.0),
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

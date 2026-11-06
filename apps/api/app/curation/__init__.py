"""Catalog curation by code (DEC-022): no human review.

The automated publication gate (``auto_publish``) approves and publishes content as the system
account (``system``); research web candidates are promoted automatically when eligible
(``web_promotion``). ``operator`` keeps the owner's emergency takedown and the release-gate
summary behind ``/v1/admin``. Validators (``closure_rules``, ``facts``) and the chunk embedder
(``embedding``) are shared with ingestion. This package must not import ``app.api`` or
``app.agents`` (import-linter contract).
"""

from app.curation.embedding import (
    ChunkEmbedder,
    DisabledEmbedder,
    Embedding,
    GeminiChunkEmbedder,
)
from app.curation.operator import OperatorService

__all__ = [
    "ChunkEmbedder",
    "DisabledEmbedder",
    "Embedding",
    "GeminiChunkEmbedder",
    "OperatorService",
]

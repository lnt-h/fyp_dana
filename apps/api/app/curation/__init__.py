"""Curator domain services behind ``/v1/admin`` (T-06).

Services take an ``AsyncSession`` and the acting curator's account id, own their unit of work
(commit at the end of each write) and append ``catalog_audit_events`` for every write except
publish/withdraw, which the SQL functions audit themselves. The only model call is the chunk
embedder (``app.curation.embedding``). This package must not import ``app.api`` or
``app.agents`` (import-linter contract).
"""

from app.curation.candidates import CandidateService
from app.curation.catalog_admin import CatalogAdminService
from app.curation.chunks import ChunkService
from app.curation.closure_rules import ClosureRuleService
from app.curation.embedding import (
    ChunkEmbedder,
    DisabledEmbedder,
    Embedding,
    GeminiChunkEmbedder,
)
from app.curation.facts import FactService
from app.curation.web_candidates import WebCandidateService

__all__ = [
    "CandidateService",
    "CatalogAdminService",
    "ChunkEmbedder",
    "ChunkService",
    "ClosureRuleService",
    "DisabledEmbedder",
    "Embedding",
    "FactService",
    "GeminiChunkEmbedder",
    "WebCandidateService",
]

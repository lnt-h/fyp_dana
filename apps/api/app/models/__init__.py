"""All ORM models. Importing this package registers every table on ``Base.metadata``.

Migrations are hand-written from docs/04-design/data/schema.sql; these models mirror their
columns, keys, foreign keys and unique constraints. CHECK constraints, partial/GIN/GiST/HNSW
indexes, triggers, views and functions live only in the migrations, so never apply
`alembic revision --autogenerate` output unedited.
"""

from app.models.account import Account
from app.models.ai import AIInvocation, AIQuotaLedger
from app.models.caches import (
    PlacesLookupCache,
    QueryEmbeddingCache,
    ResearchCache,
    RoutesMatrixCache,
)
from app.models.catalog import (
    CatalogAuditEvent,
    CatalogPublication,
    FactEvidence,
    MediaAsset,
    Place,
    PlaceAlias,
    PlaceClosureRule,
    PlaceFact,
    PlaceLocalization,
    PlaceMedia,
    PublicationFact,
    PublicationMedia,
    Source,
    SourceRevision,
    WebPlaceCandidate,
)
from app.models.guide import GuideMessage, GuideMessageCitation, GuideSession
from app.models.knowledge import KnowledgeChunk, KnowledgeChunkSource
from app.models.planning import (
    AccountDeletionJob,
    AccountPreferences,
    IdempotencyRecord,
    PlanPreview,
    PreviewRevision,
    RouteLeg,
    Trip,
    TripDay,
    TripStop,
)
from app.models.providers import (
    DataProvider,
    ExternalPlaceIdentity,
    ImportRecord,
    ImportRun,
    ProviderFieldRule,
    ProviderPolicy,
)
from app.models.reference import Area, Category, City, FactField
from app.models.study import StudyParticipant, StudySessionLog

__all__ = [
    "AIInvocation",
    "AIQuotaLedger",
    "Account",
    "AccountDeletionJob",
    "AccountPreferences",
    "Area",
    "CatalogAuditEvent",
    "CatalogPublication",
    "Category",
    "City",
    "DataProvider",
    "ExternalPlaceIdentity",
    "FactEvidence",
    "FactField",
    "GuideMessage",
    "GuideMessageCitation",
    "GuideSession",
    "IdempotencyRecord",
    "ImportRecord",
    "ImportRun",
    "KnowledgeChunk",
    "KnowledgeChunkSource",
    "MediaAsset",
    "Place",
    "PlaceAlias",
    "PlaceClosureRule",
    "PlaceFact",
    "PlaceLocalization",
    "PlaceMedia",
    "PlacesLookupCache",
    "PlanPreview",
    "PreviewRevision",
    "ProviderFieldRule",
    "ProviderPolicy",
    "PublicationFact",
    "PublicationMedia",
    "QueryEmbeddingCache",
    "ResearchCache",
    "RouteLeg",
    "RoutesMatrixCache",
    "Source",
    "SourceRevision",
    "StudyParticipant",
    "StudySessionLog",
    "Trip",
    "TripDay",
    "TripStop",
    "WebPlaceCandidate",
]

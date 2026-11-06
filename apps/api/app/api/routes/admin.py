"""Curator API ``/v1/admin`` (API-033..042 from openapi 0.4.0 plus the 1.0 curator surfaces).

Every route requires the curator role (``require_curator``, 403 ``curator_role_required``).
Writes resolve the curator's internal account for audit rows. Business rules live in
``app.curation``; this module only binds HTTP to the services.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.curation import (
    CandidateService,
    CatalogAdminService,
    ChunkEmbedder,
    ChunkService,
    ClosureRuleService,
    FactService,
    GeminiChunkEmbedder,
    WebCandidateService,
)
from app.curation.candidates import CandidateSort
from app.db.session import get_db_session, session_factory
from app.models.account import Account
from app.schemas.admin import (
    AdminPlaceFact,
    AdminPlaceFactList,
    CandidateCreate,
    CandidateDetail,
    CandidatePage,
    CandidateReview,
    CatalogPublication,
    ChunkInput,
    ChunkSaveResult,
    ChunkUpdate,
    CitySummaryList,
    ClosureAppliesTo,
    ClosureReviewState,
    ClosureRule,
    ClosureRuleCreate,
    ClosureRuleList,
    ClosureRuleUpdate,
    FactCreate,
    FactReview,
    FactUpdate,
    ImportRun,
    ImportRunPage,
    KnowledgeChunkList,
    PublishRequest,
    Source,
    SourceCreate,
    SourcePage,
    SourceRevision,
    SourceRevisionCreate,
    SourceRevisionList,
    UnpublishRequest,
    WebCandidate,
    WebCandidatePage,
    WebCandidateReview,
    WebCandidateReviewState,
    WorkflowState,
)
from app.schemas.common import ErrorResponse
from app.security.curator import get_curator_account, require_curator

_ERRORS: dict[int | str, dict[str, Any]] = {
    code: {"model": ErrorResponse} for code in (400, 401, 403, 404, 409, 422, 503)
}

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_curator)],
    responses=_ERRORS,
)

Session = Annotated[AsyncSession, Depends(get_db_session)]
Curator = Annotated[Account, Depends(get_curator_account)]
AppSettings = Annotated[Settings, Depends(get_settings)]
Cursor = Annotated[str | None, Query(max_length=512)]
Limit = Annotated[int, Query(ge=1, le=50)]
OptionalIdempotencyKey = Annotated[uuid.UUID | None, Header(alias="Idempotency-Key")]
RequiredIdempotencyKey = Annotated[uuid.UUID, Header(alias="Idempotency-Key")]


def get_chunk_embedder(settings: AppSettings) -> ChunkEmbedder:
    return GeminiChunkEmbedder(settings, session_factory)


Embedder = Annotated[ChunkEmbedder, Depends(get_chunk_embedder)]


def _candidates(
    session: AsyncSession, embedder: ChunkEmbedder, settings: Settings
) -> CandidateService:
    return CandidateService(session, embedder, default_city_code=settings.default_city_code)


# ---- Candidates (API-033..037) ------------------------------------------------------------


@router.get("/candidates", response_model=CandidatePage, operation_id="adminListCandidates")
async def list_candidates(
    session: Session,
    embedder: Embedder,
    settings: AppSettings,
    city_id: uuid.UUID | None = None,
    workflow_state: WorkflowState | None = None,
    import_run_id: uuid.UUID | None = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
    sort: CandidateSort = "-updated_at",
    cursor: Cursor = None,
    limit: Limit = 20,
) -> CandidatePage:
    return await _candidates(session, embedder, settings).list_candidates(
        city_id=city_id,
        workflow_state=workflow_state,
        import_run_id=import_run_id,
        q=q,
        sort=sort,
        cursor=cursor,
        limit=limit,
    )


@router.post(
    "/candidates",
    response_model=CandidateDetail,
    status_code=status.HTTP_201_CREATED,
    operation_id="adminCreateCandidate",
)
async def create_candidate(
    body: CandidateCreate,
    session: Session,
    curator: Curator,
    embedder: Embedder,
    settings: AppSettings,
    idempotency_key: OptionalIdempotencyKey = None,
) -> CandidateDetail:
    return await _candidates(session, embedder, settings).create_candidate(body, curator.id)


@router.get(
    "/candidates/{place_id}", response_model=CandidateDetail, operation_id="adminGetCandidate"
)
async def get_candidate(
    place_id: uuid.UUID, session: Session, embedder: Embedder, settings: AppSettings
) -> CandidateDetail:
    return await _candidates(session, embedder, settings).get_candidate(place_id)


@router.patch(
    "/candidates/{place_id}", response_model=CandidateDetail, operation_id="adminReviewCandidate"
)
async def review_candidate(
    place_id: uuid.UUID,
    body: CandidateReview,
    session: Session,
    curator: Curator,
    embedder: Embedder,
    settings: AppSettings,
    idempotency_key: OptionalIdempotencyKey = None,
) -> CandidateDetail:
    return await _candidates(session, embedder, settings).review_candidate(
        place_id, body, curator.id
    )


@router.post(
    "/candidates/{place_id}/publish",
    response_model=CatalogPublication,
    status_code=status.HTTP_201_CREATED,
    operation_id="adminPublishCandidate",
)
async def publish_candidate(
    place_id: uuid.UUID,
    body: PublishRequest,
    session: Session,
    curator: Curator,
    embedder: Embedder,
    settings: AppSettings,
    idempotency_key: RequiredIdempotencyKey,
) -> CatalogPublication:
    return await _candidates(session, embedder, settings).publish(place_id, body, curator.id)


@router.post(
    "/places/{place_id}/unpublish",
    response_model=CatalogPublication,
    operation_id="adminUnpublishPlace",
)
async def unpublish_place(
    place_id: uuid.UUID,
    body: UnpublishRequest,
    session: Session,
    curator: Curator,
    embedder: Embedder,
    settings: AppSettings,
    idempotency_key: RequiredIdempotencyKey,
) -> CatalogPublication:
    return await _candidates(session, embedder, settings).unpublish(place_id, body, curator.id)


# ---- Facts --------------------------------------------------------------------------------


@router.get(
    "/places/{place_id}/facts", response_model=AdminPlaceFactList, operation_id="adminListFacts"
)
async def list_facts(
    place_id: uuid.UUID,
    session: Session,
    field_code: Annotated[str | None, Query(max_length=64)] = None,
    include_history: bool = True,
) -> AdminPlaceFactList:
    return await FactService(session).list_facts(
        place_id, field_code=field_code, include_history=include_history
    )


@router.post(
    "/places/{place_id}/facts",
    response_model=AdminPlaceFact,
    status_code=status.HTTP_201_CREATED,
    operation_id="adminCreateFact",
)
async def create_fact(
    place_id: uuid.UUID, body: FactCreate, session: Session, curator: Curator
) -> AdminPlaceFact:
    return await FactService(session).create_fact(place_id, body, curator.id)


@router.patch(
    "/places/{place_id}/facts/{fact_id}",
    response_model=AdminPlaceFact,
    operation_id="adminUpdateFact",
)
async def update_fact(
    place_id: uuid.UUID, fact_id: uuid.UUID, body: FactUpdate, session: Session, curator: Curator
) -> AdminPlaceFact:
    return await FactService(session).update_fact(place_id, fact_id, body, curator.id)


@router.post(
    "/places/{place_id}/facts/{fact_id}/review",
    response_model=AdminPlaceFact,
    operation_id="adminReviewFact",
)
async def review_fact(
    place_id: uuid.UUID, fact_id: uuid.UUID, body: FactReview, session: Session, curator: Curator
) -> AdminPlaceFact:
    return await FactService(session).review_fact(place_id, fact_id, body, curator.id)


# ---- Closure rules ------------------------------------------------------------------------


def _rules(session: AsyncSession, settings: Settings) -> ClosureRuleService:
    return ClosureRuleService(session, default_city_code=settings.default_city_code)


@router.get(
    "/places/{place_id}/closure-rules",
    response_model=ClosureRuleList,
    operation_id="adminListPlaceClosureRules",
)
async def list_place_closure_rules(
    place_id: uuid.UUID,
    session: Session,
    settings: AppSettings,
    review_state: ClosureReviewState | None = None,
) -> ClosureRuleList:
    return await _rules(session, settings).list_rules(place_id=place_id, review_state=review_state)


@router.post(
    "/places/{place_id}/closure-rules",
    response_model=ClosureRule,
    status_code=status.HTTP_201_CREATED,
    operation_id="adminCreatePlaceClosureRule",
)
async def create_place_closure_rule(
    place_id: uuid.UUID,
    body: ClosureRuleCreate,
    session: Session,
    curator: Curator,
    settings: AppSettings,
) -> ClosureRule:
    return await _rules(session, settings).create_rule(body, curator.id, place_id=place_id)


@router.get("/closure-rules", response_model=ClosureRuleList, operation_id="adminListClosureRules")
async def list_closure_rules(
    session: Session,
    settings: AppSettings,
    city_id: uuid.UUID | None = None,
    applies_to: ClosureAppliesTo | None = None,
    area_code: Annotated[str | None, Query(max_length=64)] = None,
    place_id: uuid.UUID | None = None,
    review_state: ClosureReviewState | None = None,
) -> ClosureRuleList:
    return await _rules(session, settings).list_rules(
        city_id=city_id,
        applies_to=applies_to,
        area_code=area_code,
        place_id=place_id,
        review_state=review_state,
    )


@router.post(
    "/closure-rules",
    response_model=ClosureRule,
    status_code=status.HTTP_201_CREATED,
    operation_id="adminCreateClosureRule",
)
async def create_closure_rule(
    body: ClosureRuleCreate, session: Session, curator: Curator, settings: AppSettings
) -> ClosureRule:
    return await _rules(session, settings).create_rule(body, curator.id)


@router.get(
    "/closure-rules/{rule_id}", response_model=ClosureRule, operation_id="adminGetClosureRule"
)
async def get_closure_rule(
    rule_id: uuid.UUID, session: Session, settings: AppSettings
) -> ClosureRule:
    return await _rules(session, settings).get_rule(rule_id)


@router.patch(
    "/closure-rules/{rule_id}", response_model=ClosureRule, operation_id="adminUpdateClosureRule"
)
async def update_closure_rule(
    rule_id: uuid.UUID,
    body: ClosureRuleUpdate,
    session: Session,
    curator: Curator,
    settings: AppSettings,
) -> ClosureRule:
    return await _rules(session, settings).update_rule(rule_id, body, curator.id)


@router.delete(
    "/closure-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    operation_id="adminDeleteClosureRule",
)
async def delete_closure_rule(
    rule_id: uuid.UUID, session: Session, curator: Curator, settings: AppSettings
) -> Response:
    await _rules(session, settings).delete_rule(rule_id, curator.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---- Chunks -------------------------------------------------------------------------------


@router.get(
    "/places/{place_id}/chunks", response_model=KnowledgeChunkList, operation_id="adminListChunks"
)
async def list_chunks(
    place_id: uuid.UUID,
    session: Session,
    embedder: Embedder,
    corpus_revision: Annotated[int | None, Query(ge=1)] = None,
) -> KnowledgeChunkList:
    return await ChunkService(session, embedder).list_chunks(
        place_id, corpus_revision=corpus_revision
    )


@router.post(
    "/places/{place_id}/chunks",
    response_model=ChunkSaveResult,
    status_code=status.HTTP_201_CREATED,
    operation_id="adminSaveChunk",
)
async def save_chunk(
    place_id: uuid.UUID, body: ChunkInput, session: Session, curator: Curator, embedder: Embedder
) -> ChunkSaveResult:
    return await ChunkService(session, embedder).save_chunk(place_id, body, curator.id)


@router.patch(
    "/places/{place_id}/chunks/{chunk_id}",
    response_model=ChunkSaveResult,
    operation_id="adminUpdateChunk",
)
async def update_chunk(
    place_id: uuid.UUID,
    chunk_id: uuid.UUID,
    body: ChunkUpdate,
    session: Session,
    curator: Curator,
    embedder: Embedder,
) -> ChunkSaveResult:
    return await ChunkService(session, embedder).update_chunk(place_id, chunk_id, body, curator.id)


# ---- Web candidates (API-046..049) --------------------------------------------------------


@router.get(
    "/web-candidates", response_model=WebCandidatePage, operation_id="adminListWebCandidates"
)
async def list_web_candidates(
    session: Session,
    review_state: WebCandidateReviewState | None = "PENDING",
    city_id: uuid.UUID | None = None,
    cursor: Cursor = None,
    limit: Limit = 20,
) -> WebCandidatePage:
    return await WebCandidateService(session).list_candidates(
        review_state=review_state, city_id=city_id, cursor=cursor, limit=limit
    )


@router.get(
    "/web-candidates/{candidate_id}",
    response_model=WebCandidate,
    operation_id="adminGetWebCandidate",
)
async def get_web_candidate(candidate_id: uuid.UUID, session: Session) -> WebCandidate:
    return await WebCandidateService(session).get_candidate(candidate_id)


@router.patch(
    "/web-candidates/{candidate_id}",
    response_model=WebCandidate,
    operation_id="adminReviewWebCandidate",
)
async def review_web_candidate(
    candidate_id: uuid.UUID,
    body: WebCandidateReview,
    session: Session,
    curator: Curator,
    idempotency_key: OptionalIdempotencyKey = None,
) -> WebCandidate:
    return await WebCandidateService(session).review(candidate_id, body, curator.id)


# ---- Imports, sources, city summary (API-038..042) ----------------------------------------


@router.get("/imports", response_model=ImportRunPage, operation_id="adminListImportRuns")
async def list_import_runs(
    session: Session,
    city_id: uuid.UUID | None = None,
    cursor: Cursor = None,
    limit: Limit = 20,
) -> ImportRunPage:
    return await CatalogAdminService(session).list_import_runs(
        city_id=city_id, cursor=cursor, limit=limit
    )


@router.get("/imports/{import_run_id}", response_model=ImportRun, operation_id="adminGetImportRun")
async def get_import_run(import_run_id: uuid.UUID, session: Session) -> ImportRun:
    return await CatalogAdminService(session).get_import_run(import_run_id)


@router.get("/sources", response_model=SourcePage, operation_id="adminListSources")
async def list_sources(session: Session, cursor: Cursor = None, limit: Limit = 20) -> SourcePage:
    return await CatalogAdminService(session).list_sources(cursor=cursor, limit=limit)


@router.post(
    "/sources",
    response_model=Source,
    status_code=status.HTTP_201_CREATED,
    operation_id="adminCreateSource",
)
async def create_source(
    body: SourceCreate,
    session: Session,
    curator: Curator,
    idempotency_key: OptionalIdempotencyKey = None,
) -> Source:
    return await CatalogAdminService(session).create_source(body, curator.id)


@router.get("/sources/{source_id}", response_model=Source, operation_id="adminGetSource")
async def get_source(source_id: uuid.UUID, session: Session) -> Source:
    return await CatalogAdminService(session).get_source(source_id)


@router.get(
    "/sources/{source_id}/revisions",
    response_model=SourceRevisionList,
    operation_id="adminListSourceRevisions",
)
async def list_source_revisions(source_id: uuid.UUID, session: Session) -> SourceRevisionList:
    return await CatalogAdminService(session).list_source_revisions(source_id)


@router.post(
    "/sources/{source_id}/revisions",
    response_model=SourceRevision,
    status_code=status.HTTP_201_CREATED,
    operation_id="adminCreateSourceRevision",
)
async def create_source_revision(
    source_id: uuid.UUID, body: SourceRevisionCreate, session: Session, curator: Curator
) -> SourceRevision:
    return await CatalogAdminService(session).create_source_revision(source_id, body, curator.id)


@router.get("/cities/summary", response_model=CitySummaryList, operation_id="adminGetCitySummary")
async def city_summary(session: Session) -> CitySummaryList:
    return await CatalogAdminService(session).city_summary()

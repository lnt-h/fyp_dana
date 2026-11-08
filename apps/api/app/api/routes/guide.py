"""Guide sessions and questions (API-024..028, ADR-010, DEC-017)."""

import asyncio
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.responses import JSONResponse

from app.api.routes.trips import errors
from app.api.sse import ProgressSink, sse_response, stream_sink
from app.guide.service import ERROR_STATUS, AskCommand, CollectingSink, GuideService
from app.models.account import Account
from app.observability import error_payload
from app.schemas.guide import (
    GuideMessage,
    GuideMessagePage,
    GuideQuestion,
    GuideSession,
    GuideSessionCreate,
)
from app.security.clerk import get_current_account
from app.trips import idempotency

router = APIRouter(prefix="/ai", tags=["guide"])

# Answers keep running when the client disconnects (the result is stored and read back with
# API-027); the set keeps a reference to every detached run until it finishes.
_DETACHED: set[asyncio.Task[None]] = set()


def get_guide_service() -> GuideService:
    """FastAPI dependency: the Guide service over the app's session factory and settings."""
    from app.config import get_settings
    from app.db.session import session_factory
    from app.guide.embedding import GeminiQueryEmbedder
    from app.guide.repository import sql_unit_of_work
    from app.guide.retrieval import HybridRetriever

    settings = get_settings()
    return GuideService(
        settings=settings,
        uow=sql_unit_of_work(session_factory),
        session_factory=session_factory,
        retriever=HybridRetriever(GeminiQueryEmbedder(settings, session_factory)),
    )


Service = Annotated[GuideService, Depends(get_guide_service)]
CurrentAccount = Annotated[Account, Depends(get_current_account)]


@router.post(
    "/sessions",
    operation_id="createGuideSession",
    response_model=GuideSession,
    status_code=status.HTTP_201_CREATED,
    responses=errors(404, 409, 422),
)
async def create_guide_session(
    body: GuideSessionCreate, service: Service, account: CurrentAccount
) -> GuideSession:
    return await service.create_session(account.id, body)


@router.get(
    "/sessions/{session_id}",
    operation_id="getGuideSession",
    response_model=GuideSession,
    responses=errors(404, 409),
)
async def get_guide_session(
    session_id: uuid.UUID, service: Service, account: CurrentAccount
) -> GuideSession:
    return await service.get_session(account.id, session_id)


@router.delete(
    "/sessions/{session_id}",
    operation_id="deleteGuideSession",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=errors(404, 409),
)
async def delete_guide_session(
    session_id: uuid.UUID, service: Service, account: CurrentAccount
) -> Response:
    await service.delete_session(account.id, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/sessions/{session_id}/messages",
    operation_id="listGuideMessages",
    response_model=GuideMessagePage,
    responses=errors(400, 404, 409),
)
async def list_guide_messages(
    session_id: uuid.UUID,
    service: Service,
    account: CurrentAccount,
    cursor: Annotated[str | None, Query(max_length=512)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> GuideMessagePage:
    return await service.list_messages(account.id, session_id, cursor=cursor, limit=limit)


@router.post(
    "/sessions/{session_id}/messages",
    operation_id="askGuide",
    responses={
        **errors(404, 409, 422, 429),
        200: {
            "model": GuideMessage,
            "description": (
                "Answer stream (text/event-stream, GuideStreamEvent) or, with Accept "
                "application/json, the completed answer."
            ),
        },
    },
)
async def ask_guide(
    session_id: uuid.UUID,
    body: GuideQuestion,
    request: Request,
    service: Service,
    account: CurrentAccount,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> Response:
    key = idempotency.normalize_key(idempotency_key, required=False)
    command = AskCommand(
        account_id=account.id,
        session_id=session_id,
        question=body,
        idempotency_key=key,
        request_id=request.state.request_id,
    )
    if "text/event-stream" in request.headers.get("accept", ""):
        sink = ProgressSink()
        task = asyncio.ensure_future(service.ask(command, sink))
        _DETACHED.add(task)
        task.add_done_callback(_DETACHED.discard)

        async def run() -> None:
            await asyncio.shield(task)

        return sse_response(
            stream_sink(sink, run(), request_id=command.request_id), request=request
        )
    collector = CollectingSink()
    await service.ask(command, collector)
    return _json_result(collector, command.request_id)


def _json_result(collector: CollectingSink, request_id: str) -> JSONResponse:
    terminal = collector.terminal()
    if terminal is None:
        return JSONResponse(
            status_code=503,
            content=error_payload(
                "internal_error", "The Guide run ended without a result", request_id, retryable=True
            ),
        )
    if terminal["type"] == "error":
        detail: dict[str, Any] = terminal["error"]
        return JSONResponse(
            status_code=ERROR_STATUS.get(str(detail.get("code", "")), 503),
            content={"error": detail},
        )
    return JSONResponse(status_code=200, content=terminal["message"])

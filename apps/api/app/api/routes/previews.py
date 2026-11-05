"""Plan previews, manual edits, regeneration shell and Save (API-018..023)."""

import uuid
from collections.abc import Mapping
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.routes.trips import Service, errors
from app.api.sse import ProgressSink, sse_response, stream_sink
from app.models.account import Account
from app.observability import error_payload
from app.planning.workflows import (
    PlanningWorkflow,
    ProposeTripCommand,
    RegenerateDayCommand,
    get_planning_workflow,
)
from app.schemas.trips import (
    AcceptPreviewRequest,
    Locale,
    PlanPreview,
    PlanPreviewCreate,
    PlanPreviewEdit,
    RegenerateDayRequest,
    TripDetail,
)
from app.security.clerk import get_current_account
from app.trips import idempotency

router = APIRouter(tags=["planning"])

Workflow = Annotated[PlanningWorkflow, Depends(get_planning_workflow)]
IdempotencyKeyHeader = Annotated[str | None, Header(alias="Idempotency-Key")]

# Terminal ``error`` codes → HTTP status in JSON mode.
ERROR_STATUS: dict[str, int] = {
    "not_implemented": 501,
    "quota_exceeded": 429,
    "revision_conflict": 409,
    "unsupported_request": 422,
    "validation_failed": 422,
}


class _CollectingSink:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def emit(self, event: BaseModel | Mapping[str, Any]) -> None:
        data = event.model_dump(mode="json") if isinstance(event, BaseModel) else dict(event)
        self.events.append(data)

    def close(self) -> None:
        return None


def _wants_stream(request: Request) -> bool:
    return "text/event-stream" in request.headers.get("accept", "")


async def _json_result(sink: _CollectingSink, service: Service, request: Request) -> Response:
    terminal = next(
        (
            event
            for event in reversed(sink.events)
            if event.get("type") in ("preview_ready", "clarification_required", "error")
        ),
        None,
    )
    if terminal is None:
        return JSONResponse(
            status_code=503,
            content=error_payload(
                "internal_error",
                "The planning run ended without a result",
                request.state.request_id,
                retryable=True,
            ),
        )
    if terminal["type"] == "error":
        detail = terminal["error"]
        return JSONResponse(
            status_code=ERROR_STATUS.get(detail.get("code", ""), 503),
            content={"error": detail},
        )
    if terminal["type"] == "clarification_required":
        return JSONResponse(status_code=200, content=terminal.get("clarification", {}))
    preview_id = uuid.UUID(str(terminal["preview_id"]))
    preview = await service.get_preview(preview_id, None, None)
    return JSONResponse(
        status_code=201,
        content=preview.model_dump(mode="json"),
        headers={"Location": f"/v1/plan-previews/{preview_id}"},
    )


@router.post(
    "/trips/{trip_id}/plan-previews",
    status_code=status.HTTP_201_CREATED,
    responses={
        **errors(404, 409, 422, 429, 501),
        200: {"description": "Clarification (JSON) or the PlanningStreamEvent stream (SSE)."},
        201: {"model": PlanPreview, "description": "Preview created (JSON mode)."},
    },
)
async def create_plan_preview(
    trip_id: uuid.UUID,
    body: PlanPreviewCreate,
    request: Request,
    service: Service,
    workflow: Workflow,
    account: Annotated[Account, Depends(get_current_account)],
    idempotency_key: IdempotencyKeyHeader = None,
) -> Response:
    """M2 shell: owner and body are validated; the injected workflow (stub until M3) runs."""
    key = idempotency.normalize_key(idempotency_key, required=False)
    trip = await service.owned_trip(trip_id)
    command = ProposeTripCommand(
        account_id=account.id,
        trip_id=trip.id,
        request=body,
        idempotency_key=key,
        request_id=request.state.request_id,
    )
    if _wants_stream(request):
        sink = ProgressSink()
        return sse_response(
            stream_sink(sink, workflow.propose_trip(command, sink), request_id=command.request_id),
            request=request,
        )
    collector = _CollectingSink()
    await workflow.propose_trip(command, collector)
    return await _json_result(collector, service, request)


@router.get("/plan-previews/{preview_id}", response_model=PlanPreview, responses=errors(404, 410))
async def get_plan_preview(
    preview_id: uuid.UUID,
    service: Service,
    revision: Annotated[int | None, Query(ge=1)] = None,
    locale: Annotated[Locale | None, Query()] = None,
) -> PlanPreview:
    return await service.get_preview(preview_id, revision, locale)


@router.patch(
    "/plan-previews/{preview_id}",
    response_model=PlanPreview,
    responses=errors(404, 409, 410, 422),
)
async def edit_plan_preview(
    preview_id: uuid.UUID,
    body: PlanPreviewEdit,
    service: Service,
    idempotency_key: IdempotencyKeyHeader = None,
) -> PlanPreview:
    """Manual edit: no AI, no routing, no solver (M3). Re-timing is a sequential shift."""
    # Validated per the contract; replay safety comes from expected_revision (a repeated edit
    # answers 409). idempotency_records has no PREVIEW_EDIT operation.
    idempotency.normalize_key(idempotency_key, required=False)
    return await service.edit_preview(preview_id, body)


@router.delete(
    "/plan-previews/{preview_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=errors(404),
)
async def discard_plan_preview(preview_id: uuid.UUID, service: Service) -> Response:
    await service.discard_preview(preview_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/plan-previews/{preview_id}/regenerate",
    status_code=status.HTTP_201_CREATED,
    responses={
        **errors(404, 409, 410, 422, 429, 501),
        200: {"description": "PlanningStreamEvent stream (SSE)."},
        201: {"model": PlanPreview, "description": "New head revision (JSON mode)."},
    },
)
async def regenerate_plan_day(
    preview_id: uuid.UUID,
    body: RegenerateDayRequest,
    request: Request,
    service: Service,
    workflow: Workflow,
    account: Annotated[Account, Depends(get_current_account)],
    idempotency_key: IdempotencyKeyHeader = None,
) -> Response:
    key = idempotency.normalize_key(idempotency_key, required=False)
    preview = await service.owned_preview(preview_id)
    command = RegenerateDayCommand(
        account_id=account.id,
        preview_id=preview.id,
        trip_id=preview.trip_id,
        request=body,
        idempotency_key=key,
        request_id=request.state.request_id,
    )
    if _wants_stream(request):
        sink = ProgressSink()
        return sse_response(
            stream_sink(
                sink, workflow.regenerate_day(command, sink), request_id=command.request_id
            ),
            request=request,
        )
    collector = _CollectingSink()
    await workflow.regenerate_day(command, collector)
    return await _json_result(collector, service, request)


@router.post(
    "/plan-previews/{preview_id}/accept",
    response_model=TripDetail,
    responses=errors(404, 409, 410, 422),
)
async def accept_plan_preview(
    preview_id: uuid.UUID,
    body: AcceptPreviewRequest,
    service: Service,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> JSONResponse:
    """Save (explicit only). Header ``Idempotency-Key`` (UUID) is required; a replay answers the
    stored 200 body with ``Idempotent-Replayed: true``."""
    result = await service.accept_preview(preview_id, body, idempotency_key)
    return JSONResponse(
        status_code=200,
        content=result.body,
        headers={idempotency.REPLAYED_HEADER: "true" if result.replayed else "false"},
    )

"""Operator API ``/v1/admin`` after DEC-022 (curator review surfaces withdrawn).

Only two routes remain, both behind the operator role (``require_curator``, configured with
``GONARRA_CURATOR_CLERK_USER_IDS``): the owner's emergency takedown (API-037) and the release-gate
city summary (API-042). Content is imported and published by the CLI pipeline
(``python -m app.cli pipeline run``), never through HTTP.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.curation import OperatorService
from app.db.session import get_db_session
from app.models.account import Account
from app.schemas.admin import CatalogPublication, CitySummaryList, UnpublishRequest
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
Operator = Annotated[Account, Depends(get_curator_account)]
RequiredIdempotencyKey = Annotated[uuid.UUID, Header(alias="Idempotency-Key")]


@router.post(
    "/places/{place_id}/unpublish",
    response_model=CatalogPublication,
    operation_id="adminUnpublishPlace",
)
async def unpublish_place(
    place_id: uuid.UUID,
    body: UnpublishRequest,
    session: Session,
    operator: Operator,
    idempotency_key: RequiredIdempotencyKey,
) -> CatalogPublication:
    return await OperatorService(session).unpublish(place_id, body, operator.id)


@router.get("/cities/summary", response_model=CitySummaryList, operation_id="adminGetCitySummary")
async def city_summary(session: Session) -> CitySummaryList:
    return await OperatorService(session).city_summary()

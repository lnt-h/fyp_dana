"""Account deletion request and status (API-006, API-007; FR-071, FR-072).

These two routes skip the ``deletion_in_progress`` guard: once a job is open they are the only
authenticated ``/v1`` surface (POST returns the open job, GET its status).
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.routes.trips import DeletionService, errors
from app.schemas.trips import AccountDeletionRequest, AccountDeletionStatus

router = APIRouter(tags=["identity"])


@router.post(
    "/me/deletion",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AccountDeletionStatus,
    responses=errors(422),
)
async def request_account_deletion(
    body: AccountDeletionRequest, service: DeletionService
) -> JSONResponse:
    """Creates (or returns the open) deletion job; the purge runs in
    ``uv run python -m app.cli run-deletion-jobs``."""
    job, _ = await service.request_deletion()
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=job.model_dump(mode="json"),
        headers={"Location": "/v1/me/deletion"},
    )


@router.get("/me/deletion", response_model=AccountDeletionStatus, responses=errors(404))
async def get_account_deletion_status(service: DeletionService) -> AccountDeletionStatus:
    return await service.deletion_status()

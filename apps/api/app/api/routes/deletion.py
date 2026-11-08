"""Account deletion request and status (API-006, API-007; FR-071, FR-072).

These two routes skip the ``deletion_in_progress`` guard: once a job is open they are the only
authenticated ``/v1`` surface (POST returns the open job, GET its status).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.routes.trips import DeletionService, errors
from app.config import DEMO_SHARED_SUBJECT
from app.errors import conflict
from app.models.account import Account
from app.schemas.trips import AccountDeletionRequest, AccountDeletionStatus
from app.security.clerk import get_account_allowing_deletion

router = APIRouter(tags=["identity"])


@router.post(
    "/me/deletion",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AccountDeletionStatus,
    responses=errors(409, 422),
)
async def request_account_deletion(
    body: AccountDeletionRequest,
    service: DeletionService,
    account: Annotated[Account, Depends(get_account_allowing_deletion)],
) -> JSONResponse:
    """Creates (or returns the open) deletion job; the purge runs in
    ``uv run python -m app.cli run-deletion-jobs``. The shared demo account (demo builds) is
    refused with ``409 demo_account_not_deletable``: every unsigned demo caller shares it."""
    if account.clerk_user_id == DEMO_SHARED_SUBJECT:
        raise conflict(
            "demo_account_not_deletable",
            "The shared demo account cannot be deleted; sign in to delete your own account",
        )
    job, _ = await service.request_deletion()
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=job.model_dump(mode="json"),
        headers={"Location": "/v1/me/deletion"},
    )


@router.get("/me/deletion", response_model=AccountDeletionStatus, responses=errors(404))
async def get_account_deletion_status(service: DeletionService) -> AccountDeletionStatus:
    return await service.deletion_status()

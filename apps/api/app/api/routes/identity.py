from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.account import Account
from app.schemas.common import ErrorResponse
from app.schemas.identity import IdentityResponse
from app.security.clerk import AuthenticatedUser, get_current_account, get_current_user

router = APIRouter(tags=["identity"])


@router.get(
    "/me",
    response_model=IdentityResponse,
    responses={401: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def read_identity(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    account: Annotated[Account, Depends(get_current_account)],
) -> IdentityResponse:
    return IdentityResponse(
        account_id=account.id,
        subject=user.subject,
        session_id=user.session_id,
    )

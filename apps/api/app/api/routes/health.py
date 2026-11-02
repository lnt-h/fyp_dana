from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.common import ErrorResponse, ServiceStatus

router = APIRouter(tags=["operations"])


@router.get("/health", response_model=ServiceStatus)
async def health() -> ServiceStatus:
    return ServiceStatus(status="ok")


@router.get("/ready", response_model=ServiceStatus, responses={503: {"model": ErrorResponse}})
async def readiness(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ServiceStatus:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable"
        ) from exc
    return ServiceStatus(status="ready")

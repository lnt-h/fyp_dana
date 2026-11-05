"""Traveler preferences (openapi.yaml API-004, API-005). Always the caller's own account."""

from datetime import time
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.catalog.preferences import PreferencesRecord, PreferencesRepository, PreferencesUpdate
from app.catalog.reference import ReferenceRepository, normalize_category_code
from app.db.session import get_db_session
from app.models.account import Account
from app.schemas.common import ErrorResponse
from app.schemas.preferences import Preferences, PreferencesWrite
from app.security.clerk import get_current_account

router = APIRouter(tags=["identity"])

Session = Annotated[AsyncSession, Depends(get_db_session)]
CurrentAccount = Annotated[Account, Depends(get_current_account)]


def _hhmm(value: time | None) -> str | None:
    return None if value is None else value.strftime("%H:%M")


def _parse_hhmm(value: str | None) -> time | None:
    return None if value is None else time.fromisoformat(value)


def _preferences(record: PreferencesRecord) -> Preferences:
    return Preferences.model_validate(
        {
            "locale": record.locale,
            "pace": record.pace,
            "interest_category_codes": list(record.interest_category_codes),
            "allowed_modes": list(record.allowed_modes),
            "day_start_time": _hhmm(record.day_start_time),
            "day_end_time": _hhmm(record.day_end_time),
            "ai_notice_acknowledged_at": record.ai_notice_acknowledged_at,
            "updated_at": record.updated_at,
        }
    )


@router.get(
    "/me/preferences",
    response_model=Preferences,
    responses={401: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def get_preferences(account: CurrentAccount, session: Session) -> Preferences:
    """Saved preferences, or defaults (vi, WALK+DRIVE) when none were saved."""
    return _preferences(await PreferencesRepository(session).get_or_default(account.id))


@router.put(
    "/me/preferences",
    response_model=Preferences,
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def put_preferences(
    body: PreferencesWrite, account: CurrentAccount, session: Session
) -> Preferences:
    """Full replace (naturally idempotent). Interest codes are case-insensitive; stored UPPER."""
    known = {category.code for category in await ReferenceRepository(session).list_categories()}
    interests: list[str] = []
    for code in body.interest_category_codes:
        normalized = normalize_category_code(code)
        if normalized not in known:
            raise ApiError(
                422,
                "validation_error",
                "Unknown interest category code",
                context={
                    "fields": [
                        {
                            "type": "value_error",
                            "location": ["body", "interest_category_codes"],
                            "message": f"unknown category code {code!r}",
                        }
                    ]
                },
            )
        if normalized not in interests:
            interests.append(normalized)
    record = await PreferencesRepository(session).upsert(
        account.id,
        PreferencesUpdate(
            locale=body.locale,
            pace=body.pace,
            interest_category_codes=tuple(interests),
            allowed_modes=tuple(body.allowed_modes),
            day_start_time=_parse_hhmm(body.day_start_time),
            day_end_time=_parse_hhmm(body.day_end_time),
            ai_notice_acknowledged=body.ai_notice_acknowledged,
        ),
    )
    return _preferences(record)

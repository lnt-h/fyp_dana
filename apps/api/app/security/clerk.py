import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.errors import AppError
from app.models.account import Account
from app.models.planning import AccountDeletionJob
from app.repositories.accounts import DeletedSubjectError, SQLAlchemyAccountRepository

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    subject: str
    session_id: str | None


class ClerkTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        if settings.jwks_url is None or settings.clerk_issuer is None:
            raise RuntimeError("Clerk issuer or JWKS URL is not configured")
        self._settings = settings
        self._client = PyJWKClient(settings.jwks_url, cache_keys=True)

    def verify(self, token: str) -> AuthenticatedUser:
        signing_key = self._client.get_signing_key_from_jwt(token)
        decode_kwargs: dict[str, Any] = {
            "algorithms": ["RS256"],
            "issuer": str(self._settings.clerk_issuer).rstrip("/"),
            "options": {"require": ["exp", "iat", "nbf", "sub"], "verify_aud": False},
        }
        if self._settings.clerk_audience:
            decode_kwargs["audience"] = self._settings.clerk_audience
            decode_kwargs["options"]["verify_aud"] = True
        claims = jwt.decode(token, signing_key.key, **decode_kwargs)
        authorized_parties = self._settings.authorized_parties
        if authorized_parties and claims.get("azp") not in authorized_parties:
            raise jwt.InvalidTokenError("Unauthorized token party")
        return AuthenticatedUser(subject=claims["sub"], session_id=claims.get("sid"))


@lru_cache
def get_token_verifier() -> ClerkTokenVerifier:
    return ClerkTokenVerifier(get_settings())


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    try:
        return await run_in_threadpool(get_token_verifier().verify, credentials.credentials)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        ) from exc
    except PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        ) from exc


def require_owner(owner_subject: str, user: AuthenticatedUser) -> None:
    if owner_subject != user.subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")


OPEN_DELETION_STATUSES = ("REQUESTED", "IN_PROGRESS", "FAILED")


async def get_account_allowing_deletion(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Account:
    """The caller's account without the deletion guard.

    Only ``GET /v1/me/deletion`` and ``POST /v1/me/deletion`` use this directly; every other
    authenticated route goes through :func:`get_current_account`. A subject whose deletion
    COMPLETED is refused with 401 instead of being mapped to a fresh account.
    """
    repository = SQLAlchemyAccountRepository(session)
    try:
        return await repository.get_or_create(user.subject)
    except DeletedSubjectError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        ) from exc


async def has_open_deletion_job(session: AsyncSession, account_id: uuid.UUID) -> bool:
    """One lookup, served by the partial unique index on open jobs
    (``uq_account_deletion_jobs_account_id_open``)."""
    statement = select(
        exists().where(
            AccountDeletionJob.account_id == account_id,
            AccountDeletionJob.status.in_(OPEN_DELETION_STATUSES),
        )
    )
    return bool(await session.scalar(statement))


def deletion_in_progress() -> AppError:
    return AppError(
        409,
        "deletion_in_progress",
        "This account is being deleted; only the deletion status is available.",
    )


async def get_deletion_pending(
    account: Annotated[Account, Depends(get_account_allowing_deletion)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> bool:
    return await has_open_deletion_job(session, account.id)


async def get_current_account(
    account: Annotated[Account, Depends(get_account_allowing_deletion)],
    deletion_pending: Annotated[bool, Depends(get_deletion_pending)],
) -> Account:
    """The caller's account; 409 ``deletion_in_progress`` once a deletion job is open
    (REQUESTED, IN_PROGRESS or FAILED), so no route can read or write an account being purged.

    After COMPLETED the account row is gone; the job keeps only ``clerk_subject_sha256``, which
    :func:`get_account_allowing_deletion` uses to refuse a still-valid token of a purged subject.
    """
    if deletion_pending:
        raise deletion_in_progress()
    return account


# ---- Optional authentication (public catalog reads, 2026-11-08) ------------------------------


async def get_optional_user(request: Request) -> AuthenticatedUser | None:
    """``None`` for a guest (no bearer token); a present token must still be valid (401).

    Reads the header directly instead of through the ``HTTPBearer`` dependency so the generated
    contract does not mark these routes as requiring a token (routes declare
    ``security: [{}, HTTPBearer]`` themselves)."""
    scheme, _, token = (request.headers.get("authorization") or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token.strip())
    return await get_current_user(credentials)


async def get_optional_account(
    user: Annotated[AuthenticatedUser | None, Depends(get_optional_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Account | None:
    """The caller's account when a valid token is sent, else ``None`` (guest).

    Used only by the public catalog reads (cities, categories, place search and detail), which
    expose published catalog data and no personal data. Same rules as
    :func:`get_current_account` once a token is present (401 for a purged subject, 409
    ``deletion_in_progress`` while a deletion job is open).
    """
    if user is None:
        return None
    account = await get_account_allowing_deletion(user, session)
    if await has_open_deletion_job(session, account.id):
        raise deletion_in_progress()
    return account

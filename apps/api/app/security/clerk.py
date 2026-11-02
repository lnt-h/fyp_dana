from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.account import Account
from app.repositories.accounts import SQLAlchemyAccountRepository

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


async def get_current_account(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Account:
    repository = SQLAlchemyAccountRepository(session)
    return await repository.get_or_create(user.subject)

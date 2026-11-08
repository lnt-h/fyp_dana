"""Owner demo bypass (GONARRA_DEMO_SHARED_USER): unsigned callers share one demo account."""

import uuid
from typing import Annotated, Any

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.config import DEMO_SHARED_SUBJECT, Settings, get_settings
from app.main import create_app
from app.models.account import Account
from app.repositories.accounts import SQLAlchemyAccountRepository
from app.security import clerk
from app.security.clerk import AuthenticatedUser, get_current_account, get_current_user
from app.security.curator import is_curator


def _settings(**overrides: Any) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


def _app(settings: Settings) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings

    # /v1/me echoes the resolved user; the account is stubbed so no database is needed.
    async def account(
        user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> Account:
        return Account(id=uuid.uuid4(), clerk_user_id=user.subject)

    app.dependency_overrides[get_current_account] = account
    return app


async def _get(app: FastAPI, path: str, **kwargs: Any) -> Any:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path, **kwargs)


async def test_bypass_off_requires_token() -> None:
    response = await _get(_app(_settings()), "/v1/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


async def test_bypass_on_without_token_is_demo_user(monkeypatch: pytest.MonkeyPatch) -> None:
    def no_verifier() -> None:
        raise AssertionError("the verifier must not be built when no token is sent")

    monkeypatch.setattr(clerk, "get_token_verifier", no_verifier)
    # No Clerk issuer configured: the bypass must still work.
    app = _app(_settings(demo_shared_user=True, clerk_issuer=None))
    response = await _get(app, "/v1/me")
    assert response.status_code == 200
    assert response.json()["subject"] == DEMO_SHARED_SUBJECT
    assert response.json()["session_id"] is None


async def test_bypass_on_with_token_uses_verifier(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    class FakeVerifier:
        def verify(self, token: str) -> AuthenticatedUser:
            seen.append(token)
            return AuthenticatedUser(subject="user_real", session_id="sess_1")

    monkeypatch.setattr(clerk, "get_token_verifier", FakeVerifier)
    app = _app(_settings(demo_shared_user=True))
    response = await _get(app, "/v1/me", headers={"Authorization": "Bearer tok_abc"})
    assert response.status_code == 200
    assert response.json()["subject"] == "user_real"
    assert seen == ["tok_abc"]


async def test_bypass_on_with_invalid_header_is_rejected() -> None:
    # A header that is present is never treated as the demo user.
    app = _app(_settings(demo_shared_user=True))
    response = await _get(app, "/v1/me", headers={"Authorization": "Basic abc"})
    assert response.status_code == 401


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_validator_rejects_bypass_outside_demo_environments(environment: str) -> None:
    with pytest.raises(ValidationError, match="GONARRA_DEMO_SHARED_USER"):
        _settings(environment=environment, demo_shared_user=True)


@pytest.mark.parametrize("environment", ["development", "test", "demo"])
def test_validator_allows_bypass_in_demo_environments(environment: str) -> None:
    assert _settings(environment=environment, demo_shared_user=True).demo_shared_user


def test_demo_user_is_not_a_curator_unless_listed() -> None:
    demo = AuthenticatedUser(DEMO_SHARED_SUBJECT, None)
    assert not is_curator(demo, _settings(demo_shared_user=True, curator_clerk_user_ids="user_a"))
    assert is_curator(demo, _settings(curator_clerk_user_ids=DEMO_SHARED_SUBJECT))


class _Result:
    def __init__(self, value: object) -> None:
        self._value = value

    def scalar_one_or_none(self) -> object:
        return self._value


class _FakeSession:
    """No existing account; the deleted-subject lookup must not run for the demo subject."""

    def __init__(self) -> None:
        self.scalar_calls = 0
        self.committed = False

    async def scalar(self, *_: object) -> object:
        self.scalar_calls += 1
        if self.scalar_calls > 1:
            raise AssertionError("demo subject must not be checked against deleted subjects")
        return None

    async def execute(self, *_: object) -> _Result:
        return _Result(Account(id=uuid.uuid4(), clerk_user_id=DEMO_SHARED_SUBJECT))

    async def commit(self) -> None:
        self.committed = True


async def test_demo_account_is_recreated_after_deletion() -> None:
    session = _FakeSession()
    account = await SQLAlchemyAccountRepository(session).get_or_create(  # type: ignore[arg-type]
        DEMO_SHARED_SUBJECT
    )
    assert account.clerk_user_id == DEMO_SHARED_SUBJECT
    assert session.committed

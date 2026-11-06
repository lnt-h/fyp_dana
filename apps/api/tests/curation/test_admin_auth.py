"""Curator role on /v1/admin: no token → 401, non-curator → 403, curator passes (no DB)."""

import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.db.session import get_db_session
from app.errors import AppError
from app.main import create_app
from app.models.account import Account
from app.security.clerk import AuthenticatedUser, get_current_user
from app.security.curator import (
    get_curator_account,
    is_curator,
    require_active_curator,
    require_curator,
)

CURATOR = "user_curator_1"


def _settings() -> Settings:
    return Settings(_env_file=None, curator_clerk_user_ids=f" {CURATOR} , user_other ")  # type: ignore[call-arg]


class _NoDb:
    async def execute(self, *_: object, **__: object) -> None:
        raise AssertionError("the role check must run before any database access")


async def _no_db() -> AsyncIterator[_NoDb]:
    yield _NoDb()


def _app(subject: str | None) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_db_session] = _no_db
    if subject is not None:
        app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(subject, None)
    return app


async def _call(app: FastAPI, method: str, path: str, **kwargs: Any) -> Any:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


def test_curator_subjects_parse_comma_separated_list() -> None:
    settings = _settings()
    assert settings.curator_subjects == frozenset({CURATOR, "user_other"})
    assert is_curator(AuthenticatedUser(CURATOR, None), settings)
    assert not is_curator(AuthenticatedUser("user_x", None), settings)
    empty = Settings(_env_file=None)  # type: ignore[call-arg]
    assert empty.curator_subjects == frozenset()


async def test_missing_token_is_401() -> None:
    response = await _call(_app(None), "GET", "/v1/admin/cities/summary")
    assert response.status_code == 401


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/v1/admin/cities/summary"),
        ("POST", f"/v1/admin/places/{uuid.uuid4()}/unpublish"),
    ],
)
async def test_non_curator_is_403_before_database(method: str, path: str) -> None:
    response = await _call(_app("user_traveler"), method, path)
    assert response.status_code == 403
    body = response.json()["error"]
    assert body["code"] == "curator_role_required"
    assert body["request_id"] == response.headers["x-request-id"]


async def test_curator_passes_role_check_and_reaches_validation() -> None:
    app = _app(CURATOR)
    app.dependency_overrides[get_curator_account] = lambda: Account(
        id=uuid.uuid4(), clerk_user_id=CURATOR
    )
    app.dependency_overrides[require_active_curator] = lambda: AuthenticatedUser(CURATOR, None)
    response = await _call(
        app,
        "POST",
        f"/v1/admin/places/{uuid.uuid4()}/unpublish",
        json={"state_reason": ""},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


# DEC-022: the curator review surfaces are gone (404 for unknown paths, 405 for a method).
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/v1/admin/candidates"),
        ("POST", "/v1/admin/candidates"),
        ("GET", f"/v1/admin/candidates/{uuid.uuid4()}"),
        ("PATCH", f"/v1/admin/candidates/{uuid.uuid4()}"),
        ("POST", f"/v1/admin/candidates/{uuid.uuid4()}/publish"),
        ("GET", "/v1/admin/web-candidates"),
        ("PATCH", f"/v1/admin/web-candidates/{uuid.uuid4()}"),
        ("GET", f"/v1/admin/places/{uuid.uuid4()}/facts"),
        ("POST", f"/v1/admin/places/{uuid.uuid4()}/facts/{uuid.uuid4()}/review"),
        ("GET", "/v1/admin/closure-rules"),
        ("DELETE", f"/v1/admin/closure-rules/{uuid.uuid4()}"),
        ("POST", f"/v1/admin/places/{uuid.uuid4()}/chunks"),
        ("GET", "/v1/admin/imports"),
        ("GET", "/v1/admin/sources"),
        ("GET", f"/v1/admin/places/{uuid.uuid4()}/unpublish"),
    ],
)
async def test_withdrawn_review_routes_are_gone(method: str, path: str) -> None:
    response = await _call(_app(CURATOR), method, path)
    assert response.status_code in (404, 405)


async def test_require_curator_returns_user() -> None:
    user = AuthenticatedUser(CURATOR, "sess")
    assert await require_curator(user, _settings()) is user


class _ScalarDb:
    def __init__(self, value: bool) -> None:
        self.value = value

    async def scalar(self, *_: object, **__: object) -> bool:
        return self.value


async def test_require_active_curator_refuses_open_deletion_job() -> None:
    user = AuthenticatedUser(CURATOR, "sess")
    assert await require_active_curator(user, _ScalarDb(False)) is user  # type: ignore[arg-type]
    with pytest.raises(AppError) as raised:
        await require_active_curator(user, _ScalarDb(True))  # type: ignore[arg-type]
    assert raised.value.status_code == 409
    assert raised.value.code == "deletion_in_progress"

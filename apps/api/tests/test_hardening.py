"""API hardening: log privacy, NUL characters, catch-all errors, fail-safe environment, demo
account deletion, provider-policy environments and the cache retention sweep."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import APIRouter, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError

from app.api.routes.trips import get_deletion_service
from app.config import DEMO_SHARED_SUBJECT, Settings
from app.db.retention import sweep_caches
from app.db.session import engine
from app.main import API_VERSION, create_app
from app.models.account import Account
from app.security.clerk import get_account_allowing_deletion


def _settings(**overrides: Any) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[call-arg]


async def _call(app: FastAPI, method: str, path: str, **kwargs: Any) -> Any:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


# ---- 1. log privacy --------------------------------------------------------------------------


def test_engine_hides_bound_parameters_in_errors() -> None:
    assert engine.sync_engine.hide_parameters is True
    error = DBAPIError.instance(
        "SELECT 1 WHERE q = %(q)s",
        {"q": "my secret question at 16.0544,108.2022"},
        Exception("boom"),
        Exception,
        hide_parameters=engine.sync_engine.hide_parameters,
    )
    assert "secret question" not in str(error) and "16.0544" not in str(error)


# ---- 2. NUL characters and the catch-all handler ----------------------------------------------


@pytest.mark.parametrize(
    "path", ["/v1/places?q=%00", "/v1/places?category_code=%00", "/v1/places?q=a%00b&limit=5"]
)
async def test_nul_in_query_parameter_is_422(path: str) -> None:
    response = await _call(create_app(), "GET", path)
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error" and body["request_id"]
    assert body["context"]["fields"][0]["type"] == "string_nul_character"
    assert body["context"]["fields"][0]["location"][0] == "query"


@pytest.mark.parametrize(
    ("path", "payload", "location"),
    [
        (
            f"/v1/ai/sessions/{uuid.uuid4()}/messages",
            {"content": "giờ mở cửa\u0000?", "input_mode": "TEXT"},
            ["body", "content"],
        ),
        (
            f"/v1/trips/{uuid.uuid4()}/plan-previews",
            {
                "source": "GENERATE",
                "expected_trip_revision": 0,
                "locale": "vi",
                "request_text": "hai ngày\u0000",
            },
            ["body", "request_text"],
        ),
        (
            "/v1/trips",
            {"city_id": str(uuid.uuid4()), "title": "x\u0000", "start_date": "2026-12-01"},
            ["body", "title"],
        ),
    ],
)
async def test_nul_in_json_body_text_is_422_before_auth_or_db(
    path: str, payload: dict[str, Any], location: list[str]
) -> None:
    response = await _call(create_app(), "POST", path, json=payload)
    assert response.status_code == 422, response.text
    fields = response.json()["error"]["context"]["fields"]
    assert fields[0]["location"] == location


async def test_text_without_nul_still_reaches_normal_validation() -> None:
    response = await _call(create_app(), "GET", "/v1/places?limit=0")
    assert response.status_code == 422
    assert response.json()["error"]["context"]["fields"][0]["type"] != "string_nul_character"


async def test_unhandled_exception_is_json_internal_error_without_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app()
    router = APIRouter()

    @router.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret user question 16.0544,108.2022")

    app.include_router(router)
    with caplog.at_level(logging.INFO):
        response = await _call(app, "GET", "/boom", headers={"X-Request-ID": "req-boom"})
    assert response.status_code == 500
    assert response.headers["content-type"] == "application/json"
    assert response.headers["x-request-id"] == "req-boom"
    error = response.json()["error"]
    assert error["code"] == "internal_error" and error["request_id"] == "req-boom"
    assert "secret" not in response.text
    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert "secret" not in logged and "16.0544" not in logged
    assert any(
        json.loads(r.getMessage()).get("event") == "unhandled_exception"
        for r in caplog.records
        if r.getMessage().startswith("{")
    )


def test_app_version_matches_documented_contract() -> None:
    assert create_app().version == API_VERSION == "1.0.4"


# ---- 3. fail-safe environment and the demo account ------------------------------------------


def test_unset_environment_is_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GONARRA_ENVIRONMENT")
    settings = _settings()
    assert settings.environment == "production"
    assert not settings.estimates_allowed and not settings.draft_policies_allowed
    with pytest.raises(ValidationError):
        _settings(demo_shared_user=True)


@pytest.mark.parametrize("environment", ["development", "test", "demo"])
def test_demo_user_and_draft_policies_allowed_outside_production(environment: str) -> None:
    settings = _settings(environment=environment, demo_shared_user=True)
    assert settings.demo_shared_user and settings.draft_policies_allowed


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_demo_user_and_draft_policies_refused_in_staging_and_production(
    environment: str,
) -> None:
    assert not _settings(environment=environment).draft_policies_allowed
    with pytest.raises(ValidationError):
        _settings(environment=environment, demo_shared_user=True)


def test_clerk_secret_key_is_a_secret() -> None:
    settings = _settings(clerk_secret_key="sk_test_123")
    assert settings.clerk_secret_key is not None
    assert "sk_test_123" not in repr(settings) and "sk_test_123" not in str(settings)


async def test_demo_account_deletion_is_refused() -> None:
    app = create_app()

    def no_service() -> None:
        raise AssertionError("no deletion job may be created for the demo account")

    app.dependency_overrides[get_account_allowing_deletion] = lambda: Account(
        id=uuid.uuid4(), clerk_user_id=DEMO_SHARED_SUBJECT
    )
    app.dependency_overrides[get_deletion_service] = lambda: object()
    response = await _call(app, "POST", "/v1/me/deletion", json={"confirm": True})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "demo_account_not_deletable"


# ---- 7. cache retention sweep -----------------------------------------------------------------


class _Result:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class _SweepSession:
    def __init__(self, *, missing: set[str] = frozenset()) -> None:  # type: ignore[assignment]
        self.missing = missing
        self.statements: list[tuple[str, dict[str, Any]]] = []
        self.committed = False

    async def scalar(self, statement: Any, params: dict[str, Any]) -> bool:
        return params["name"].removeprefix("public.") not in self.missing

    async def execute(self, statement: Any, params: dict[str, Any]) -> _Result:
        self.statements.append((str(statement), params))
        return _Result(2)

    async def commit(self) -> None:
        self.committed = True


async def test_cache_sweep_deletes_expired_rows_and_clears_old_coordinates() -> None:
    now = datetime(2026, 11, 9, tzinfo=UTC)
    session = _SweepSession(missing={"query_embedding_cache"})
    report = await sweep_caches(session, now=now)  # type: ignore[arg-type]
    assert session.committed
    sql = [statement for statement, _ in session.statements]
    assert sql[0].startswith("UPDATE places_lookup_cache SET location = NULL")
    assert session.statements[0][1]["cutoff"] == datetime(2026, 10, 10, tzinfo=UTC)
    assert any(s.startswith("DELETE FROM research_cache WHERE expires_at <=") for s in sql)
    assert any(s.startswith("DELETE FROM routes_matrix_cache WHERE expires_at <=") for s in sql)
    assert any("places_lookup_cache WHERE outcome_expires_at <=" in s for s in sql)
    assert not any("query_embedding_cache" in s for s in sql)
    assert report.skipped == ["query_embedding_cache"]
    assert report.places_locations_cleared == 2
    assert report.deleted == {
        "research_cache": 2,
        "routes_matrix_cache": 2,
        "places_lookup_cache": 2,
    }


def test_caches_sweep_command_is_registered() -> None:
    from typer.testing import CliRunner

    from app.cli import app as cli

    result = CliRunner().invoke(cli, ["caches", "--help"])
    assert result.exit_code == 0 and "sweep" in result.output


# ---- 8. integration tests never touch a non-test database ---------------------------------------


def test_integration_database_guard(pytestconfig: pytest.Config) -> None:
    guard = next(
        plugin.integration_db_allowed
        for plugin in pytestconfig.pluginmanager.get_plugins()
        if hasattr(plugin, "integration_db_allowed")
    )
    base = "postgresql+psycopg://gonarra:gonarra@localhost:5432/"
    assert not guard(base + "gonarra", override=None)
    assert not guard(base + "gonarra_testing", override=None)
    assert not guard(base + "gonarra_it3x", override=None)
    for name in ("gonarra_test", "gonarra_it", "gonarra_ci", "gonarra_it3"):
        assert guard(base + name, override=None)
    assert guard(base + "gonarra", override="1")
    assert not guard(base + "gonarra", override="true")


def test_unit_tests_never_read_the_developer_env_file() -> None:
    from app.config import get_settings

    settings = get_settings()
    assert Settings.model_config["env_file"] is None
    assert settings.environment == "test" and not settings.demo_shared_user

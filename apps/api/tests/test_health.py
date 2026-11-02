from collections.abc import AsyncIterator

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db_session
from app.main import create_app


class ReadySession:
    async def execute(self, _: object) -> None:
        return None


class UnavailableSession:
    async def execute(self, _: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("offline"))


async def ready_session() -> AsyncIterator[ReadySession]:
    yield ReadySession()


async def unavailable_session() -> AsyncIterator[UnavailableSession]:
    yield UnavailableSession()


async def request(app: FastAPI, path: str):  # type: ignore[arg-type]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path)


async def test_health_is_live_without_database() -> None:
    response = await request(create_app(), "/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "gonarra-api"}


async def test_request_id_rejects_unbounded_client_value() -> None:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health", headers={"X-Request-ID": "x" * 129})
    assert response.status_code == 200
    assert response.headers["x-request-id"] != "x" * 129


async def test_readiness_checks_database() -> None:
    app = create_app()
    app.dependency_overrides[get_db_session] = ready_session
    response = await request(app, "/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_readiness_returns_503_when_database_is_unavailable() -> None:
    app = create_app()
    app.dependency_overrides[get_db_session] = unavailable_session
    response = await request(app, "/ready")
    assert response.status_code == 503
    assert response.json()["error"]["message"] == "Database unavailable"
    assert response.json()["error"]["retryable"] is True

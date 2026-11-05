import json
import logging
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from starlette.types import Message

from app.main import create_app
from app.observability import RequestContextMiddleware


async def get(path: str, headers: dict[str, str] | None = None) -> Any:
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path, headers=headers)


async def test_request_id_is_generated_when_absent() -> None:
    response = await get("/health")
    assert response.status_code == 200
    uuid.UUID(response.headers["x-request-id"])


async def test_valid_client_request_id_is_echoed() -> None:
    response = await get("/health", headers={"X-Request-ID": "mobile-1.2:abc_DEF"})
    assert response.headers["x-request-id"] == "mobile-1.2:abc_DEF"


@pytest.mark.parametrize("supplied", ["x" * 129, "has space", "semi;colon"])
async def test_invalid_client_request_id_is_replaced(supplied: str) -> None:
    response = await get("/health", headers={"X-Request-ID": supplied})
    assert response.headers["x-request-id"] != supplied
    uuid.UUID(response.headers["x-request-id"])


async def test_error_envelope_carries_request_id() -> None:
    response = await get("/does-not-exist", headers={"X-Request-ID": "req-404"})
    assert response.status_code == 404
    assert response.headers["x-request-id"] == "req-404"
    assert response.json()["error"]["code"] == "resource_not_found"
    assert response.json()["error"]["request_id"] == "req-404"


async def test_request_is_logged_as_json(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="gonarra.request"):
        await get("/health", headers={"X-Request-ID": "req-log"})
    lines = [json.loads(r.getMessage()) for r in caplog.records if r.name == "gonarra.request"]
    assert lines == [
        {
            "request_id": "req-log",
            "method": "GET",
            "path": "/health",
            "status": 200,
            "duration_ms": lines[0]["duration_ms"],
        }
    ]


async def test_non_http_scopes_pass_through_untouched() -> None:
    seen: list[dict[str, Any]] = []

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        seen.append(scope)
        await send({"type": "lifespan.startup.complete"})

    sent: list[Message] = []

    async def receive() -> Message:
        return {"type": "lifespan.startup"}

    async def send(message: Message) -> None:
        sent.append(message)

    scope: dict[str, Any] = {"type": "lifespan", "asgi": {"version": "3.0"}}
    await RequestContextMiddleware(inner)(scope, receive, send)
    assert seen == [{"type": "lifespan", "asgi": {"version": "3.0"}}]
    assert sent == [{"type": "lifespan.startup.complete"}]


async def test_app_lifespan_runs_under_middleware() -> None:
    app = create_app()
    messages: list[Message] = []
    inbox = iter([{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}])

    async def receive() -> Message:
        return next(inbox)

    async def send(message: Message) -> None:
        messages.append(message)

    await app({"type": "lifespan", "asgi": {"version": "3.0"}, "state": {}}, receive, send)
    assert [m["type"] for m in messages] == [
        "lifespan.startup.complete",
        "lifespan.shutdown.complete",
    ]

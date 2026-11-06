import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any, Literal

from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from starlette.types import Message

from app.api.sse import ProgressSink, format_event, sse_response, stream_sink
from app.main import create_app


class StageEvent(BaseModel):
    type: Literal["progress", "preview_ready", "error"]
    stage: str | None = None
    preview_revision: int | None = None


def parse(body: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in body.split("\n\n"):
        if not block or block.startswith(":"):
            continue
        name_line, data_line = block.split("\n")
        assert name_line.startswith("event: ") and data_line.startswith("data: ")
        events.append((name_line[len("event: ") :], json.loads(data_line[len("data: ") :])))
    return events


def app_with(route: Any) -> FastAPI:
    app = create_app()
    app.add_api_route("/test-stream", route, methods=["GET"])
    return app


async def fetch(app: FastAPI) -> tuple[int, dict[str, str], str]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream("GET", "/test-stream", headers={"X-Request-ID": "req-sse"}) as r:
            body = "".join([chunk async for chunk in r.aiter_text()])
            return r.status_code, dict(r.headers), body


def test_format_event_omits_top_level_nulls() -> None:
    assert format_event(StageEvent(type="progress", stage="ROUTING")) == (
        b'event: progress\ndata: {"type":"progress","stage":"ROUTING"}\n\n'
    )


async def test_events_stream_in_order_with_names_and_headers() -> None:
    async def run(sink: ProgressSink) -> None:
        sink.emit(StageEvent(type="progress", stage="VALIDATING_REQUEST"))
        await asyncio.sleep(0)
        sink.emit(StageEvent(type="progress", stage="SELECTING_PLACES"))
        sink.emit({"type": "preview_ready", "preview_revision": 1})
        sink.close()

    async def route(request: Request) -> StreamingResponse:
        sink = ProgressSink()
        return sse_response(stream_sink(sink, run(sink)), request=request)

    status, headers, body = await fetch(app_with(route))
    assert status == 200
    assert headers["content-type"].startswith("text/event-stream")
    assert headers["cache-control"] == "no-cache"
    assert headers["x-accel-buffering"] == "no"
    assert headers["x-request-id"] == "req-sse"
    assert parse(body) == [
        ("progress", {"type": "progress", "stage": "VALIDATING_REQUEST"}),
        ("progress", {"type": "progress", "stage": "SELECTING_PLACES"}),
        ("preview_ready", {"type": "preview_ready", "preview_revision": 1}),
    ]


async def test_run_finishing_without_close_drains_queue() -> None:
    async def run(sink: ProgressSink) -> None:
        sink.emit({"type": "progress", "stage": "ROUTING"})
        sink.emit({"type": "preview_ready"})

    async def route(request: Request) -> StreamingResponse:
        sink = ProgressSink()
        return sse_response(stream_sink(sink, run(sink)), request=request)

    _, _, body = await fetch(app_with(route))
    assert [name for name, _ in parse(body)] == ["progress", "preview_ready"]


async def test_heartbeat_is_sent_while_idle() -> None:
    async def events() -> AsyncIterator[StageEvent]:
        await asyncio.sleep(0.2)
        yield StageEvent(type="preview_ready")

    async def route(request: Request) -> StreamingResponse:
        return sse_response(events(), request=request, heartbeat_seconds=0.02)

    _, _, body = await fetch(app_with(route))
    assert body.startswith(": keep-alive\n\n")
    assert body.count(": keep-alive\n\n") >= 2
    assert parse(body) == [("preview_ready", {"type": "preview_ready"})]


async def test_failing_run_ends_with_terminal_error_event() -> None:
    async def run(sink: ProgressSink) -> None:
        sink.emit(StageEvent(type="progress", stage="ROUTING"))
        raise RuntimeError("solver exploded")

    async def route(request: Request) -> StreamingResponse:
        sink = ProgressSink()
        rid = request.state.request_id
        return sse_response(stream_sink(sink, run(sink), request_id=rid), request=request)

    status, _, body = await fetch(app_with(route))
    assert status == 200
    events = parse(body)
    assert events[0] == ("progress", {"type": "progress", "stage": "ROUTING"})
    name, payload = events[-1]
    assert name == "error"
    assert payload["error"]["request_id"] == "req-sse"
    assert payload["error"]["code"] == "internal_error"
    assert "solver exploded" not in body


async def test_client_disconnect_cancels_run_without_raising() -> None:
    """Drive the ASGI app directly: the first event must reach the client before the run
    finishes (no buffering under the middleware), and a disconnect cancels the run."""
    run_cancelled = asyncio.Event()
    first_sent = asyncio.Event()

    async def run(sink: ProgressSink) -> None:
        sink.emit(StageEvent(type="progress", stage="VALIDATING_REQUEST"))
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            run_cancelled.set()
            raise

    async def route(request: Request) -> StreamingResponse:
        sink = ProgressSink()
        return sse_response(stream_sink(sink, run(sink)), request=request, heartbeat_seconds=60)

    app = app_with(route)
    sent: list[Message] = []
    request_delivered = False

    async def receive() -> Message:
        nonlocal request_delivered
        if not request_delivered:
            request_delivered = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await first_sent.wait()
        return {"type": "http.disconnect"}

    async def send(message: Message) -> None:
        sent.append(message)
        if message["type"] == "http.response.body" and message.get("body"):
            first_sent.set()

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/test-stream",
        "raw_path": b"/test-stream",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"test")],
        "client": ("127.0.0.1", 1),
        "server": ("test", 80),
    }
    await asyncio.wait_for(app(scope, receive, send), timeout=5)
    await asyncio.wait_for(run_cancelled.wait(), timeout=1)
    start = sent[0]
    assert start["type"] == "http.response.start"
    assert dict(start["headers"])[b"x-request-id"]
    bodies = [m["body"] for m in sent if m["type"] == "http.response.body" and m.get("body")]
    assert bodies == [format_event(StageEvent(type="progress", stage="VALIDATING_REQUEST"))]

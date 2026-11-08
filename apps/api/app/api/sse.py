"""Server-Sent Events helpers for streamed planning and Guide routes (architecture §3.2, §5).

The orchestrator emits one event per step into a :class:`ProgressSink`; the route drains it with
:func:`stream_sink` and returns :func:`sse_response`. Every event is a Pydantic model (or mapping)
with a ``type`` field; the SSE ``event:`` name equals ``type`` and ``data:`` is the JSON payload
(``PlanningStreamEvent`` / ``GuideStreamEvent`` in ``docs/04-design/api/openapi.yaml``).
"""

import asyncio
import contextlib
import json
import logging
from collections.abc import AsyncIterator, Coroutine, Mapping
from typing import Any, Final

from fastapi import Request
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.observability import error_payload

logger = logging.getLogger("gonarra.sse")

SSEEvent = BaseModel | Mapping[str, Any]

SSE_HEADERS: Final[dict[str, str]] = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}
HEARTBEAT_COMMENT: Final[bytes] = b": keep-alive\n\n"


class _Closed:
    pass


_CLOSED: Final = _Closed()


class ProgressSink:
    """Single-consumer event channel between an orchestrator run and its SSE route."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[SSEEvent | _Closed] = asyncio.Queue()
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    def emit(self, event: SSEEvent) -> None:
        """Queue one event. Events emitted after :meth:`close` are dropped."""
        if self._closed:
            return
        self._queue.put_nowait(event)

    def close(self) -> None:
        """Mark the end of the stream. Idempotent."""
        if self._closed:
            return
        self._closed = True
        self._queue.put_nowait(_CLOSED)

    async def _get(self) -> SSEEvent | _Closed:
        return await self._queue.get()

    def _get_nowait(self) -> SSEEvent | _Closed | None:
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None


def event_payload(event: SSEEvent) -> dict[str, Any]:
    """JSON-ready payload. Top-level ``None`` fields are omitted (the stream event schemas mark
    them optional, not nullable); nested nulls are kept."""
    if isinstance(event, BaseModel):
        data: dict[str, Any] = event.model_dump(mode="json", by_alias=True)
    else:
        data = json.loads(json.dumps(dict(event), default=str))
    return {key: value for key, value in data.items() if value is not None}


def format_event(event: SSEEvent) -> bytes:
    """Serialise one event as ``event: <type>\\ndata: <json>\\n\\n``."""
    payload = event_payload(event)
    event_type = payload.get("type")
    if not isinstance(event_type, str) or not event_type or "\n" in event_type:
        raise ValueError("SSE event requires a single-line string 'type' field")
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event_type}\ndata: {data}\n\n".encode()


def error_event(
    request_id: str,
    *,
    code: str = "internal_error",
    message: str = "The request could not be completed",
    retryable: bool = True,
) -> dict[str, Any]:
    """Terminal ``error`` event carrying the shared ``ErrorDetail`` envelope."""
    detail = error_payload(code, message, request_id, retryable=retryable)["error"]
    return {"type": "error", "error": detail}


async def stream_sink(
    sink: ProgressSink,
    run: Coroutine[Any, Any, Any],
    *,
    request_id: str = "",
) -> AsyncIterator[SSEEvent]:
    """Run ``run`` as a task and yield the events it emits into ``sink``.

    Stops when the sink is closed or the run finishes (remaining queued events are drained).
    If the run raises, a terminal ``error`` event is yielded instead of propagating. When the
    consumer stops early (client disconnect, cancellation), the run task is cancelled.
    """
    task: asyncio.Task[Any] = asyncio.ensure_future(run)
    try:
        while True:
            getter = asyncio.ensure_future(sink._get())
            try:
                await asyncio.wait({getter, task}, return_when=asyncio.FIRST_COMPLETED)
            finally:
                if not getter.done():
                    getter.cancel()
            if getter.done() and not getter.cancelled():
                item = getter.result()
                if isinstance(item, _Closed):
                    break
                yield item
                continue
            # The run finished without closing the sink: drain what is already queued.
            while (pending := sink._get_nowait()) is not None:
                if isinstance(pending, _Closed):
                    break
                yield pending
            break
        sink.close()
        try:
            await task
        except Exception:
            logger.exception(json.dumps({"request_id": request_id, "event": "stream_run_failed"}))
            yield error_event(request_id)
    finally:
        sink.close()
        if not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task


async def _with_heartbeat(
    events: AsyncIterator[SSEEvent],
    request: Request,
    heartbeat_seconds: float,
) -> AsyncIterator[bytes]:
    iterator = aiter(events)
    next_event: asyncio.Future[SSEEvent] | None = None
    try:
        while True:
            if next_event is None:
                next_event = asyncio.ensure_future(anext(iterator))
            done, _ = await asyncio.wait({next_event}, timeout=heartbeat_seconds)
            if not done:
                if await request.is_disconnected():
                    return
                yield HEARTBEAT_COMMENT
                continue
            try:
                event = next_event.result()
            except StopAsyncIteration:
                return
            finally:
                next_event = None
            yield format_event(event)
    finally:
        if next_event is not None and not next_event.done():
            next_event.cancel()
            with contextlib.suppress(asyncio.CancelledError, StopAsyncIteration, Exception):
                await next_event
        aclose = getattr(iterator, "aclose", None)
        if aclose is not None:
            with contextlib.suppress(Exception):
                await aclose()


def sse_response(
    events: AsyncIterator[SSEEvent],
    *,
    request: Request,
    heartbeat_seconds: float = 15.0,
) -> StreamingResponse:
    """``text/event-stream`` response with keep-alive comments while idle.

    The body is never buffered; a client disconnect ends the stream (and, via
    :func:`stream_sink`, cancels the run) without raising.
    """
    if heartbeat_seconds <= 0:
        raise ValueError("heartbeat_seconds must be positive")
    return StreamingResponse(
        _with_heartbeat(events, request, heartbeat_seconds),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )

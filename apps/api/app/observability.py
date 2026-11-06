import json
import logging
import re
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.errors import AppError

logger = logging.getLogger("gonarra.request")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def error_payload(
    code: str,
    message: str,
    request_id: str,
    *,
    retryable: bool = False,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "retryable": retryable,
            "request_id": request_id,
            "context": context or {},
        }
    }


class RequestContextMiddleware:
    """Pure ASGI request-context middleware.

    Assigns ``X-Request-ID`` (client value if it matches :data:`REQUEST_ID_PATTERN`, else a
    UUID4), exposes it as ``request.state.request_id``, echoes it on the response and logs one
    JSON line per request once the response has completed. The body is never buffered, so
    streaming responses (SSE) pass straight through. Non-HTTP scopes are untouched.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        supplied_request_id = Headers(scope=scope).get("x-request-id", "")
        request_id = (
            supplied_request_id
            if REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
            else str(uuid.uuid4())
        )
        scope.setdefault("state", {})["request_id"] = request_id
        started = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)["x-request-id"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            logger.info(
                json.dumps(
                    {
                        "request_id": request_id,
                        "method": scope["method"],
                        "path": scope["path"],
                        "status": status_code,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    }
                )
            )


def install_observability(application: FastAPI) -> None:
    application.add_middleware(RequestContextMiddleware)

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {
            401: "authentication_required",
            404: "resource_not_found",
            409: "revision_conflict",
            422: "validation_error",
            503: "service_unavailable",
        }.get(exc.status_code, "request_failed")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code,
                message,
                request.state.request_id,
                retryable=exc.status_code == 503,
            ),
        )

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                exc.code,
                exc.message,
                request.state.request_id,
                retryable=exc.retryable,
                context=exc.context,
            ),
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields = [
            {
                "type": error["type"],
                "location": list(error["loc"]),
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_payload(
                "validation_error",
                "Request validation failed",
                request.state.request_id,
                context={"fields": fields},
            ),
        )

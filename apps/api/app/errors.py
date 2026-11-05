"""Application error carrying the shared error-envelope fields (code, message, context).

Raised by domain services (``app.curation``) and dependencies; rendered by the handler that
``app.observability.install_observability`` registers. Lives outside ``app.api`` so that
domain packages can raise it without importing the HTTP layer.
"""

from typing import Any


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.context = context or {}
        self.retryable = retryable


def not_found(message: str = "Resource not found", **context: Any) -> ApiError:
    return ApiError(404, "not_found", message, context=context)


def conflict(code: str, message: str, **context: Any) -> ApiError:
    return ApiError(409, code, message, context=context)


def invalid(code: str, message: str, **context: Any) -> ApiError:
    return ApiError(422, code, message, context=context)

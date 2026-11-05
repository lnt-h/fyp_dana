"""The single application error, carrying the shared ``ErrorResponse`` envelope fields.

Raised by domain services (``app.trips``, ``app.planning``, ``app.curation``), security
dependencies and routes; rendered by the one handler that
:func:`app.observability.install_observability` registers. Lives outside ``app.api`` so that
domain packages can raise it without importing the HTTP layer.
"""

from typing import Any


class AppError(Exception):
    """An expected failure with a stable machine-readable ``code`` and optional ``context``."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        context: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.retryable = retryable
        self.context = context or {}
        self.headers = headers


def not_found(
    message: str = "Resource not found", *, code: str = "resource_not_found", **context: Any
) -> AppError:
    """404 that never discloses whether the resource exists for another owner."""
    return AppError(404, code, message, context=context)


def revision_conflict(message: str, **context: Any) -> AppError:
    return AppError(409, "revision_conflict", message, context=context)


def conflict(code: str, message: str, **context: Any) -> AppError:
    return AppError(409, code, message, context=context)


def validation_failed(code: str, message: str, **context: Any) -> AppError:
    return AppError(422, code, message, context=context)


invalid = validation_failed

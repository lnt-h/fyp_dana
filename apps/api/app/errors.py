"""Domain error carrying the shared ``ErrorResponse`` envelope fields.

Raised by services (``app.trips``, ``app.planning``) and rendered by the handler installed in
:func:`app.observability.install_observability`. Services never import the HTTP layer.
"""

from typing import Any


class AppError(Exception):
    """An expected failure with a stable machine-readable ``code``."""

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


def not_found(message: str = "Resource not found") -> AppError:
    """404 that never discloses whether the resource exists for another owner."""
    return AppError(404, "resource_not_found", message)


def revision_conflict(message: str, **context: Any) -> AppError:
    return AppError(409, "revision_conflict", message, context=context)


def validation_failed(code: str, message: str, **context: Any) -> AppError:
    return AppError(422, code, message, context=context)

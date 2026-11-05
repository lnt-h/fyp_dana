"""HTTP errors with an explicit envelope code (openapi.yaml ``ErrorDetail.code``)."""

from typing import Any

from fastapi import HTTPException


class ApiError(HTTPException):
    """An ``HTTPException`` whose ``error.code`` is set explicitly instead of from the status.

    The handler in :mod:`app.observability` reads ``error_code`` and ``context`` duck-typed.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.context = context or {}

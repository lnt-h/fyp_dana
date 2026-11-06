"""Clerk Backend API client, limited to deleting a user after an account purge (FR-071).

The secret (``GONARRA_CLERK_SECRET_KEY``) stays server-side and is never logged. Only the Clerk
user id is sent, which Clerk already holds. A 404 means the user is already gone, so the call is
idempotent and a retried deletion job can repeat it safely.
"""

from typing import Final, Protocol
from urllib.parse import quote

import httpx
from pydantic import SecretStr

from app.config import Settings

CLERK_API_BASE_URL: Final = "https://api.clerk.com/v1"
DEFAULT_TIMEOUT: Final = httpx.Timeout(10.0, connect=5.0)


class ClerkBackendError(Exception):
    """Clerk did not confirm the deletion (non-2xx other than 404, or a transport failure)."""


class ClerkUserDeleter(Protocol):
    async def delete_user(self, user_id: str) -> None: ...


class ClerkBackendClient:
    def __init__(
        self,
        secret_key: SecretStr,
        *,
        base_url: str = CLERK_API_BASE_URL,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> None:
        self._secret_key = secret_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def delete_user(self, user_id: str) -> None:
        """``DELETE /v1/users/{user_id}``; 2xx or 404 (already deleted) both count as success."""
        url = f"{self._base_url}/users/{quote(user_id, safe='')}"
        headers = {"Authorization": f"Bearer {self._secret_key.get_secret_value()}"}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.delete(url, headers=headers)
        except httpx.HTTPError as exc:
            raise ClerkBackendError(type(exc).__name__) from exc
        if response.status_code == 404 or response.is_success:
            return
        raise ClerkBackendError(f"status {response.status_code}")


def clerk_user_deleter(settings: Settings) -> ClerkBackendClient | None:
    """The configured client, or ``None`` when ``GONARRA_CLERK_SECRET_KEY`` is unset."""
    if settings.clerk_secret_key is None:
        return None
    return ClerkBackendClient(settings.clerk_secret_key)

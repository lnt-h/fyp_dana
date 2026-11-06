"""Clerk Backend user deletion (FR-071) with pytest-httpx; no live call."""

import httpx
import pytest
from pydantic import SecretStr
from pytest_httpx import HTTPXMock

from app.config import Settings
from app.security.clerk_backend import ClerkBackendClient, ClerkBackendError, clerk_user_deleter

URL = "https://api.clerk.com/v1/users/user_2abc"


@pytest.mark.parametrize("status", [200, 404])
async def test_delete_user_succeeds_on_ok_and_already_deleted(
    httpx_mock: HTTPXMock, status: int
) -> None:
    httpx_mock.add_response(method="DELETE", url=URL, status_code=status, json={})
    await ClerkBackendClient(SecretStr("sk_test_x")).delete_user("user_2abc")
    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["authorization"] == "Bearer sk_test_x"


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_delete_user_raises_on_failure(httpx_mock: HTTPXMock, status: int) -> None:
    httpx_mock.add_response(method="DELETE", url=URL, status_code=status, json={})
    with pytest.raises(ClerkBackendError) as excinfo:
        await ClerkBackendClient(SecretStr("sk_test_x")).delete_user("user_2abc")
    assert "sk_test_x" not in str(excinfo.value)


async def test_delete_user_raises_on_timeout(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ReadTimeout("slow"), method="DELETE", url=URL)
    with pytest.raises(ClerkBackendError):
        await ClerkBackendClient(SecretStr("sk_test_x")).delete_user("user_2abc")


async def test_user_id_is_path_escaped(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="DELETE", url="https://api.clerk.com/v1/users/a%2F..%2Fb", status_code=200
    )
    await ClerkBackendClient(SecretStr("sk")).delete_user("a/../b")


def test_deleter_is_none_without_secret() -> None:
    assert clerk_user_deleter(Settings(_env_file=None, clerk_secret_key="")) is None  # type: ignore[call-arg]
    configured = Settings(_env_file=None, clerk_secret_key="sk_test_y")  # type: ignore[call-arg]
    assert isinstance(clerk_user_deleter(configured), ClerkBackendClient)

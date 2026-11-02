import uuid

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.models.account import Account
from app.security.clerk import (
    AuthenticatedUser,
    get_current_account,
    get_current_user,
    require_owner,
)


async def request(app: FastAPI, path: str):  # type: ignore[arg-type]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path)


async def test_identity_requires_authentication() -> None:
    response = await request(create_app(), "/v1/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


async def test_identity_uses_verified_subject() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        subject="user_123", session_id="sess_123"
    )
    account_id = uuid.uuid4()
    app.dependency_overrides[get_current_account] = lambda: Account(
        id=account_id, clerk_user_id="user_123"
    )
    response = await request(app, "/v1/me")
    assert response.status_code == 200
    assert response.json() == {
        "account_id": str(account_id),
        "subject": "user_123",
        "session_id": "sess_123",
    }


def test_owner_check_hides_foreign_resource() -> None:
    user = AuthenticatedUser(subject="owner_a", session_id=None)
    try:
        require_owner("owner_b", user)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 404
    else:
        raise AssertionError("foreign resource should be hidden")

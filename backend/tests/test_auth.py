"""Authentication boundary tests without contacting Firebase."""

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.firebase_service import FirebaseAuthenticationError
from app.utils.auth import get_firebase_service


pytestmark = pytest.mark.asyncio


class StubFirebaseService:
    """Deterministic Firebase replacement for API tests."""

    def __init__(self, result: dict[str, Any] | Exception) -> None:
        self.result = result

    def verify_id_token(self, token: str) -> dict[str, Any]:
        assert token
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


async def request_me(token: str | None = None) -> tuple[int, dict[str, Any], str | None]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/auth/me", headers=headers)
    return response.status_code, response.json(), response.headers.get("www-authenticate")


async def test_auth_me_requires_bearer_token() -> None:
    status_code, body, authenticate_header = await request_me()

    assert status_code == 401
    assert body == {"detail": "Authentication required"}
    assert authenticate_header == "Bearer"


async def test_auth_me_rejects_invalid_token() -> None:
    app.dependency_overrides[get_firebase_service] = lambda: StubFirebaseService(
        FirebaseAuthenticationError("invalid")
    )
    try:
        status_code, body, authenticate_header = await request_me("bad-token")
    finally:
        app.dependency_overrides.clear()

    assert status_code == 401
    assert body == {"detail": "Invalid or expired authentication token"}
    assert authenticate_header == "Bearer"


async def test_auth_me_returns_verified_user() -> None:
    app.dependency_overrides[get_firebase_service] = lambda: StubFirebaseService(
        {
            "uid": "user-123",
            "email": "person@example.com",
            "email_verified": True,
        }
    )
    try:
        status_code, body, _ = await request_me("valid-token")
    finally:
        app.dependency_overrides.clear()

    assert status_code == 200
    assert body == {
        "uid": "user-123",
        "email": "person@example.com",
        "email_verified": True,
    }

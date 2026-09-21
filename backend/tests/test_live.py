"""Protected Gemini Live bootstrap API tests."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.auth import AuthenticatedUser
from app.models.live import LiveTokenResponse
from app.services.live_token_service import LiveTokenError, get_live_token_service
from app.utils.auth import get_current_user


pytestmark = pytest.mark.asyncio


class StubLiveTokenService:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail

    def create_token(self) -> LiveTokenResponse:
        if self.fail:
            raise LiveTokenError("offline")
        now = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
        return LiveTokenResponse(
            token="auth_tokens/test-token",
            model="gemini-3.8-live",
            expires_at=now + timedelta(minutes=15),
            new_session_expires_at=now + timedelta(minutes=1),
        )


def override_user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="user-123", email="person@example.com")


async def test_live_token_requires_authentication() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/live/token")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


async def test_live_token_returns_only_ephemeral_credential() -> None:
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_live_token_service] = StubLiveTokenService
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/live/token")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["token"] == "auth_tokens/test-token"
    assert body["model"] == "gemini-3.8-live"
    assert "api_key" not in body


async def test_live_token_maps_provider_failure_to_503() -> None:
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_live_token_service] = lambda: StubLiveTokenService(True)
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/live/token")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Gemini Live is temporarily unavailable"}

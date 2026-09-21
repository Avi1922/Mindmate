"""Journal route tests with Firebase and Firestore isolated."""

from datetime import datetime, timezone
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.auth import AuthenticatedUser
from app.models.journal import JournalRecord
from app.services.journal_service import get_journal_service
from app.utils.auth import get_current_user


pytestmark = pytest.mark.asyncio


class StubJournalService:
    def __init__(self) -> None:
        self.created: list[tuple[str, str]] = []
        self.limit_seen: int | None = None

    def create_journal(self, uid: str, text: str) -> JournalRecord:
        self.created.append((uid, text))
        return JournalRecord(
            id="journal-1",
            text=text,
            created_at=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
        )

    def list_journals(self, uid: str, limit: int) -> list[JournalRecord]:
        assert uid == "user-123"
        self.limit_seen = limit
        return [
            JournalRecord(
                id="journal-1",
                text="A calm afternoon.",
                created_at=datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc),
            )
        ]


def override_user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="user-123", email="person@example.com")


async def api_request(
    method: str,
    path: str,
    **kwargs: Any,
) -> tuple[int, dict[str, Any]]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.request(method, path, **kwargs)
    return response.status_code, response.json()


async def test_create_journal_is_user_scoped_and_trimmed() -> None:
    service = StubJournalService()
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_journal_service] = lambda: service
    try:
        status_code, body = await api_request(
            "POST",
            "/api/journal",
            json={"text": "  A calm afternoon.  "},
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 201
    assert body["id"] == "journal-1"
    assert body["text"] == "A calm afternoon."
    assert body["source"] == "journal"
    assert service.created == [("user-123", "A calm afternoon.")]


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
async def test_create_journal_rejects_blank_text(text: str) -> None:
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_journal_service] = StubJournalService
    try:
        status_code, body = await api_request(
            "POST",
            "/api/journal",
            json={"text": text},
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 422
    assert body["detail"]


async def test_list_journals_honors_limit() -> None:
    service = StubJournalService()
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_journal_service] = lambda: service
    try:
        status_code, body = await api_request("GET", "/api/journal?limit=5")
    finally:
        app.dependency_overrides.clear()

    assert status_code == 200
    assert body["count"] == 1
    assert body["items"][0]["text"] == "A calm afternoon."
    assert service.limit_seen == 5


async def test_journal_requires_authentication() -> None:
    status_code, body = await api_request("GET", "/api/journal")

    assert status_code == 401
    assert body == {"detail": "Authentication required"}

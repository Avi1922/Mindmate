"""Voice conversation validation and API tests."""

from datetime import UTC, datetime
from typing import Any

import pytest
from app.main import app
from app.models.auth import AuthenticatedUser
from app.models.conversation import ConversationRecord, ConversationTurn
from app.services.conversation_service import get_conversation_service
from app.utils.auth import get_current_user
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.asyncio


class StubConversationService:
    def __init__(self) -> None:
        self.created: tuple[object, ...] | None = None
        self.limit_seen: int | None = None

    def create_conversation(
        self,
        uid: str,
        turns: list[ConversationTurn],
        transcript: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> ConversationRecord:
        self.created = (uid, turns, transcript, started_at, ended_at)
        return ConversationRecord(
            id="conversation-1",
            transcript=transcript,
            turns=turns,
            started_at=started_at,
            ended_at=ended_at,
            created_at=ended_at,
        )

    def list_conversations(self, uid: str, limit: int) -> list[ConversationRecord]:
        assert uid == "user-123"
        self.limit_seen = limit
        timestamp = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
        return [
            ConversationRecord(
                id="conversation-1",
                transcript="User: I feel calmer.\nMindMate: What helped?",
                turns=[
                    {"role": "user", "text": "I feel calmer."},
                    {"role": "assistant", "text": "What helped?"},
                ],
                started_at=timestamp,
                ended_at=timestamp,
                created_at=timestamp,
            )
        ]


def override_user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="user-123", email="person@example.com")


async def api_request(method: str, path: str, **kwargs: Any) -> tuple[int, Any]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.request(method, path, **kwargs)
    return response.status_code, response.json()


async def test_create_conversation_derives_transcript_and_scopes_user() -> None:
    service = StubConversationService()
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_conversation_service] = lambda: service
    try:
        status_code, body = await api_request(
            "POST",
            "/api/conversations",
            json={
                "turns": [
                    {"role": "user", "text": "  I feel calmer.  "},
                    {"role": "assistant", "text": "What helped?"},
                ],
                "started_at": "2026-09-20T11:58:00Z",
                "ended_at": "2026-09-20T12:00:00Z",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 201
    assert body["source"] == "voice"
    assert body["transcript"] == "User: I feel calmer.\nMindMate: What helped?"
    assert service.created is not None
    assert service.created[0] == "user-123"
    assert service.created[2] == body["transcript"]


@pytest.mark.parametrize(
    "payload",
    [
        {
            "turns": [],
            "started_at": "2026-09-20T11:58:00Z",
            "ended_at": "2026-09-20T12:00:00Z",
        },
        {
            "turns": [{"role": "assistant", "text": "Hello"}],
            "started_at": "2026-09-20T11:58:00Z",
            "ended_at": "2026-09-20T12:00:00Z",
        },
        {
            "turns": [{"role": "user", "text": "Hello"}],
            "started_at": "2026-09-20T12:01:00Z",
            "ended_at": "2026-09-20T12:00:00Z",
        },
    ],
)
async def test_create_conversation_rejects_invalid_payload(
    payload: dict[str, Any],
) -> None:
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_conversation_service] = StubConversationService
    try:
        status_code, body = await api_request(
            "POST", "/api/conversations", json=payload
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 422
    assert body["detail"]


async def test_list_conversations_honors_limit() -> None:
    service = StubConversationService()
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_conversation_service] = lambda: service
    try:
        status_code, body = await api_request("GET", "/api/conversations?limit=5")
    finally:
        app.dependency_overrides.clear()

    assert status_code == 200
    assert body["count"] == 1
    assert body["items"][0]["id"] == "conversation-1"
    assert service.limit_seen == 5


async def test_conversations_require_authentication() -> None:
    status_code, body = await api_request("GET", "/api/conversations")

    assert status_code == 401
    assert body == {"detail": "Authentication required"}

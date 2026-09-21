"""Firestore conversation persistence tests."""

from datetime import datetime, timezone

from app.models.conversation import ConversationTurn
from app.services.conversation_service import ConversationService


class FakeDocument:
    def __init__(self, document_id: str) -> None:
        self.id = document_id
        self.saved: dict[str, object] | None = None

    def collection(self, name: str) -> "FakeCollection":
        assert name == "conversations"
        return FakeCollection(self)

    def set(self, payload: dict[str, object]) -> None:
        self.saved = payload


class FakeCollection:
    def __init__(self, target: FakeDocument) -> None:
        self.target = target

    def document(self, document_id: str | None = None) -> FakeDocument:
        if document_id is not None:
            assert document_id == "user-123"
        return self.target


class FakeFirestore:
    def __init__(self, target: FakeDocument) -> None:
        self.target = target

    def collection(self, name: str) -> FakeCollection:
        assert name == "users"
        return FakeCollection(self.target)


class FakeFirebase:
    def __init__(self, target: FakeDocument) -> None:
        self.firestore = FakeFirestore(target)

    def get_firestore_client(self) -> FakeFirestore:
        return self.firestore


def test_conversation_is_saved_under_verified_user_path() -> None:
    document = FakeDocument("conversation-123")
    service = ConversationService(FakeFirebase(document))  # type: ignore[arg-type]
    started_at = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    ended_at = datetime(2026, 9, 20, 12, 3, tzinfo=timezone.utc)
    turns = [ConversationTurn(role="user", text="I feel hopeful.")]

    result = service.create_conversation(
        "user-123",
        turns,
        "User: I feel hopeful.",
        started_at,
        ended_at,
    )

    assert result.id == "conversation-123"
    assert document.saved is not None
    assert document.saved["source"] == "voice"
    assert document.saved["transcript"] == "User: I feel hopeful."
    assert document.saved["turns"] == [{"role": "user", "text": "I feel hopeful."}]
    assert document.saved["startedAt"] == started_at
    assert document.saved["endedAt"] == ended_at

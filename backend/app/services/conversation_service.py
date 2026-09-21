"""User-scoped Firestore voice conversation persistence."""

from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from firebase_admin import firestore

from app.models.conversation import ConversationRecord, ConversationTurn
from app.services.firebase_service import FirebaseService, get_firebase_service


class ConversationStorageError(RuntimeError):
    """Raised when a conversation operation cannot be completed."""


class ConversationService:
    def __init__(self, firebase: FirebaseService) -> None:
        self._firebase = firebase

    def create_conversation(
        self,
        uid: str,
        turns: list[ConversationTurn],
        transcript: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> ConversationRecord:
        created_at = datetime.now(UTC)
        normalized_start = started_at.astimezone(UTC)
        normalized_end = ended_at.astimezone(UTC)
        try:
            document = (
                self._firebase.get_firestore_client()
                .collection("users")
                .document(uid)
                .collection("conversations")
                .document()
            )
            document.set(
                {
                    "source": "voice",
                    "transcript": transcript,
                    "turns": [turn.model_dump() for turn in turns],
                    "startedAt": normalized_start,
                    "endedAt": normalized_end,
                    "createdAt": created_at,
                }
            )
        except Exception as exc:
            raise ConversationStorageError("Conversation could not be saved") from exc

        return ConversationRecord(
            id=document.id,
            transcript=transcript,
            turns=turns,
            started_at=normalized_start,
            ended_at=normalized_end,
            created_at=created_at,
        )

    def list_conversations(self, uid: str, limit: int) -> list[ConversationRecord]:
        try:
            snapshots = (
                self._firebase.get_firestore_client()
                .collection("users")
                .document(uid)
                .collection("conversations")
                .order_by("createdAt", direction=firestore.Query.DESCENDING)
                .limit(limit)
                .stream()
            )
            return [self._record_from_snapshot(snapshot) for snapshot in snapshots]
        except Exception as exc:
            raise ConversationStorageError(
                "Conversation history could not be loaded"
            ) from exc

    @staticmethod
    def _record_from_snapshot(snapshot: Any) -> ConversationRecord:
        data = snapshot.to_dict() or {}
        started_at = data.get("startedAt")
        ended_at = data.get("endedAt")
        created_at = data.get("createdAt")
        if not all(
            isinstance(value, datetime) for value in (started_at, ended_at, created_at)
        ):
            raise ConversationStorageError("Stored conversation has invalid timestamps")
        assert isinstance(started_at, datetime)
        assert isinstance(ended_at, datetime)
        assert isinstance(created_at, datetime)
        return ConversationRecord(
            id=snapshot.id,
            transcript=str(data.get("transcript", "")),
            turns=data.get("turns", []),
            started_at=started_at,
            ended_at=ended_at,
            created_at=created_at,
        )


@lru_cache
def get_conversation_service() -> ConversationService:
    return ConversationService(get_firebase_service())

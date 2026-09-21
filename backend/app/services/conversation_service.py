"""User-scoped Firestore voice conversation persistence."""

from datetime import datetime, timezone
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
        created_at = datetime.now(timezone.utc)
        normalized_start = started_at.astimezone(timezone.utc)
        normalized_end = ended_at.astimezone(timezone.utc)
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
            raise ConversationStorageError("Conversation history could not be loaded") from exc

    @staticmethod
    def _record_from_snapshot(snapshot: Any) -> ConversationRecord:
        data = snapshot.to_dict() or {}
        timestamps = (data.get("startedAt"), data.get("endedAt"), data.get("createdAt"))
        if not all(isinstance(value, datetime) for value in timestamps):
            raise ConversationStorageError("Stored conversation has invalid timestamps")
        return ConversationRecord(
            id=snapshot.id,
            transcript=str(data.get("transcript", "")),
            turns=data.get("turns", []),
            started_at=timestamps[0],
            ended_at=timestamps[1],
            created_at=timestamps[2],
        )


@lru_cache
def get_conversation_service() -> ConversationService:
    return ConversationService(get_firebase_service())

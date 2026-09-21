"""User-scoped Firestore journal persistence."""

from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from firebase_admin import firestore

from app.models.journal import JournalRecord
from app.services.firebase_service import FirebaseService, get_firebase_service


class JournalStorageError(RuntimeError):
    """Raised when a journal operation cannot be completed."""


class JournalService:
    """Persist journals beneath ``users/{uid}/journals``."""

    def __init__(self, firebase: FirebaseService) -> None:
        self._firebase = firebase

    def create_journal(self, uid: str, text: str) -> JournalRecord:
        created_at = datetime.now(timezone.utc)
        try:
            document = (
                self._firebase.get_firestore_client()
                .collection("users")
                .document(uid)
                .collection("journals")
                .document()
            )
            document.set(
                {
                    "text": text,
                    "source": "journal",
                    "createdAt": created_at,
                }
            )
        except Exception as exc:
            raise JournalStorageError("Journal could not be saved") from exc

        return JournalRecord(
            id=document.id,
            text=text,
            created_at=created_at,
        )

    def list_journals(self, uid: str, limit: int) -> list[JournalRecord]:
        try:
            query = (
                self._firebase.get_firestore_client()
                .collection("users")
                .document(uid)
                .collection("journals")
                .order_by("createdAt", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            snapshots = query.stream()
            return [self._record_from_snapshot(snapshot) for snapshot in snapshots]
        except Exception as exc:
            raise JournalStorageError("Journal history could not be loaded") from exc

    @staticmethod
    def _record_from_snapshot(snapshot: Any) -> JournalRecord:
        data = snapshot.to_dict() or {}
        created_at = data.get("createdAt")
        if not isinstance(created_at, datetime):
            raise JournalStorageError("Stored journal has an invalid timestamp")

        return JournalRecord(
            id=snapshot.id,
            text=str(data.get("text", "")),
            source="journal",
            created_at=created_at,
        )


@lru_cache
def get_journal_service() -> JournalService:
    """Return the process-wide journal service."""

    return JournalService(get_firebase_service())

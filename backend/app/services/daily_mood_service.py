"""Deterministic daily aggregation and Firestore persistence."""

from collections.abc import Iterable, Mapping
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from typing import Any

from google.cloud.firestore_v1.base_query import FieldFilter

from app.models.analysis import EmotionLabel, EmotionScores
from app.models.mood import DailyMoodRecord
from app.services.firebase_service import FirebaseService, get_firebase_service


class DailyMoodNotFoundError(LookupError):
    """Raised when a date has no analyses to aggregate."""


class DailyMoodStorageError(RuntimeError):
    """Raised when daily mood data cannot be read or saved."""


def aggregate_daily_mood(
    target_date: date,
    analyses: Iterable[Mapping[str, Any]],
    *,
    updated_at: datetime | None = None,
) -> DailyMoodRecord:
    """Average equally weighted analyses into one reproducible daily record."""

    items = list(analyses)
    if not items:
        raise DailyMoodNotFoundError("No analyses exist for this date")

    labels: tuple[EmotionLabel, ...] = (
        "joy",
        "sadness",
        "anger",
        "fear",
        "neutral",
    )
    emotion_totals = {label: 0.0 for label in labels}
    mood_total = 0.0
    journal_count = 0
    conversation_count = 0

    for item in items:
        scores = EmotionScores.model_validate(item.get("emotions"))
        for label in labels:
            emotion_totals[label] += getattr(scores, label)
        mood_total += float(item["moodScore"])
        if item.get("source") == "journal":
            journal_count += 1
        elif item.get("source") == "conversation":
            conversation_count += 1

    count = len(items)
    averaged = EmotionScores(
        **{
            label: round(emotion_totals[label] / count, 4)
            for label in labels
        }
    )
    dominant = max(labels, key=lambda label: getattr(averaged, label))

    return DailyMoodRecord(
        date=target_date,
        mood_score=round(mood_total / count),
        dominant_emotion=dominant,
        emotions=averaged,
        journal_count=journal_count,
        conversation_count=conversation_count,
        analysis_count=count,
        updated_at=updated_at or datetime.now(timezone.utc),
    )


class DailyMoodService:
    def __init__(self, firebase: FirebaseService) -> None:
        self._firebase = firebase

    def rebuild(self, uid: str, target_date: date) -> DailyMoodRecord:
        """Recompute and overwrite one user's date from its source analyses."""

        start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        try:
            user = self._firebase.get_firestore_client().collection("users").document(uid)
            snapshots = (
                user.collection("analyses")
                .where(filter=FieldFilter("createdAt", ">=", start))
                .where(filter=FieldFilter("createdAt", "<", end))
                .stream()
            )
            record = aggregate_daily_mood(
                target_date,
                (snapshot.to_dict() for snapshot in snapshots),
            )
            user.collection("dailyMood").document(target_date.isoformat()).set(
                {
                    "date": record.date.isoformat(),
                    "moodScore": record.mood_score,
                    "dominantEmotion": record.dominant_emotion,
                    "emotions": record.emotions.model_dump(),
                    "journalCount": record.journal_count,
                    "conversationCount": record.conversation_count,
                    "analysisCount": record.analysis_count,
                    "updatedAt": record.updated_at,
                }
            )
            return record
        except DailyMoodNotFoundError:
            raise
        except Exception as exc:
            raise DailyMoodStorageError("Daily mood could not be rebuilt") from exc

    def get(self, uid: str, target_date: date) -> DailyMoodRecord:
        """Read one previously aggregated daily mood record."""

        try:
            snapshot = (
                self._firebase.get_firestore_client()
                .collection("users")
                .document(uid)
                .collection("dailyMood")
                .document(target_date.isoformat())
                .get()
            )
            if not snapshot.exists:
                raise DailyMoodNotFoundError("No daily mood exists for this date")
            return self._record_from_snapshot(snapshot)
        except DailyMoodNotFoundError:
            raise
        except Exception as exc:
            raise DailyMoodStorageError("Daily mood could not be loaded") from exc

    def list_recent(
        self,
        uid: str,
        days: int,
        *,
        today: date | None = None,
    ) -> list[DailyMoodRecord]:
        """Return existing records for a bounded UTC date window, oldest first."""

        current_date = today or datetime.now(timezone.utc).date()
        try:
            collection = (
                self._firebase.get_firestore_client()
                .collection("users")
                .document(uid)
                .collection("dailyMood")
            )
            records: list[DailyMoodRecord] = []
            for offset in range(days - 1, -1, -1):
                target_date = current_date - timedelta(days=offset)
                snapshot = collection.document(target_date.isoformat()).get()
                if snapshot.exists:
                    records.append(self._record_from_snapshot(snapshot))
            return records
        except Exception as exc:
            raise DailyMoodStorageError("Daily mood history could not be loaded") from exc

    @staticmethod
    def _record_from_snapshot(snapshot: Any) -> DailyMoodRecord:
        data = snapshot.to_dict() or {}
        return DailyMoodRecord(
            date=data["date"],
            mood_score=data["moodScore"],
            dominant_emotion=data["dominantEmotion"],
            emotions=data["emotions"],
            journal_count=data["journalCount"],
            conversation_count=data["conversationCount"],
            analysis_count=data["analysisCount"],
            updated_at=data["updatedAt"],
        )


@lru_cache
def get_daily_mood_service() -> DailyMoodService:
    return DailyMoodService(get_firebase_service())

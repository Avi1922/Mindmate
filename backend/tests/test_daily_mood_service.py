"""Explainable daily mood aggregation tests."""

from datetime import UTC, date, datetime

import pytest
from app.services.daily_mood_service import (
    DailyMoodNotFoundError,
    DailyMoodService,
    aggregate_daily_mood,
)


class FakeSnapshot:
    def __init__(self, data: dict[str, object] | None) -> None:
        self.exists = data is not None
        self._data = data

    def to_dict(self) -> dict[str, object] | None:
        return self._data

    def get(self) -> "FakeSnapshot":
        return self


class FakeDocument:
    def __init__(self, records: dict[str, dict[str, object]]) -> None:
        self.records = records

    def collection(self, name: str) -> "FakeCollection":
        assert name == "dailyMood"
        return FakeCollection(self.records)


class FakeCollection:
    def __init__(self, records: dict[str, dict[str, object]]) -> None:
        self.records = records

    def document(self, document_id: str) -> FakeDocument | FakeSnapshot:
        if document_id == "user-123":
            return FakeDocument(self.records)
        return FakeSnapshot(self.records.get(document_id))


class FakeFirestore:
    def __init__(self, records: dict[str, dict[str, object]]) -> None:
        self.records = records

    def collection(self, name: str) -> FakeCollection:
        assert name == "users"
        return FakeCollection(self.records)


class FakeFirebase:
    def __init__(self, records: dict[str, dict[str, object]]) -> None:
        self.firestore = FakeFirestore(records)

    def get_firestore_client(self) -> FakeFirestore:
        return self.firestore


def test_daily_aggregation_averages_scores_and_counts_sources() -> None:
    analyses = [
        {
            "source": "journal",
            "moodScore": 70,
            "emotions": {
                "joy": 0.6,
                "sadness": 0.1,
                "anger": 0.05,
                "fear": 0.05,
                "neutral": 0.2,
            },
        },
        {
            "source": "conversation",
            "moodScore": 40,
            "emotions": {
                "joy": 0.1,
                "sadness": 0.5,
                "anger": 0.1,
                "fear": 0.2,
                "neutral": 0.1,
            },
        },
        {
            "source": "journal",
            "moodScore": 55,
            "emotions": {
                "joy": 0.3,
                "sadness": 0.2,
                "anger": 0.1,
                "fear": 0.1,
                "neutral": 0.3,
            },
        },
    ]
    updated_at = datetime(2026, 9, 20, 18, 0, tzinfo=UTC)

    result = aggregate_daily_mood(date(2026, 9, 20), analyses, updated_at=updated_at)

    assert result.mood_score == 55
    assert result.emotions.joy == pytest.approx(0.3333)
    assert result.emotions.sadness == pytest.approx(0.2667)
    assert result.dominant_emotion == "joy"
    assert result.journal_count == 2
    assert result.conversation_count == 1
    assert result.analysis_count == 3
    assert result.updated_at == updated_at


def test_daily_aggregation_is_deterministic() -> None:
    analysis = {
        "source": "journal",
        "moodScore": 50,
        "emotions": {
            "joy": 0.2,
            "sadness": 0.2,
            "anger": 0.1,
            "fear": 0.1,
            "neutral": 0.4,
        },
    }
    updated_at = datetime(2026, 9, 20, tzinfo=UTC)

    first = aggregate_daily_mood(date(2026, 9, 20), [analysis], updated_at=updated_at)
    second = aggregate_daily_mood(date(2026, 9, 20), [analysis], updated_at=updated_at)

    assert first == second


def test_daily_aggregation_requires_at_least_one_analysis() -> None:
    with pytest.raises(DailyMoodNotFoundError):
        aggregate_daily_mood(date(2026, 9, 20), [])


def test_recent_history_returns_existing_days_oldest_first() -> None:
    updated_at = datetime(2026, 9, 20, 18, 0, tzinfo=UTC)

    def record(day: str, score: int) -> dict[str, object]:
        return {
            "date": day,
            "moodScore": score,
            "dominantEmotion": "neutral",
            "emotions": {
                "joy": 0.1,
                "sadness": 0.1,
                "anger": 0.1,
                "fear": 0.1,
                "neutral": 0.6,
            },
            "journalCount": 1,
            "conversationCount": 0,
            "analysisCount": 1,
            "updatedAt": updated_at,
        }

    service = DailyMoodService(
        FakeFirebase(  # type: ignore[arg-type]
            {
                "2026-09-18": record("2026-09-18", 45),
                "2026-09-20": record("2026-09-20", 60),
            }
        )
    )

    results = service.list_recent("user-123", 3, today=date(2026, 9, 20))

    assert [item.date.isoformat() for item in results] == [
        "2026-09-18",
        "2026-09-20",
    ]
    assert [item.mood_score for item in results] == [45, 60]

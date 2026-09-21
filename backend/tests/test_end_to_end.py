"""Authenticated journal and voice flows across the public API contracts."""

from datetime import date, datetime, timezone
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.analysis import AnalysisResponse
from app.models.auth import AuthenticatedUser
from app.models.conversation import ConversationRecord, ConversationTurn
from app.models.journal import JournalRecord
from app.models.mood import DailyMoodRecord
from app.services.analysis_service import get_analysis_service
from app.services.conversation_service import get_conversation_service
from app.services.daily_mood_service import aggregate_daily_mood, get_daily_mood_service
from app.services.journal_service import get_journal_service
from app.utils.auth import get_current_user


pytestmark = pytest.mark.asyncio
TEST_TIME = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)


class FlowStore:
    def __init__(self) -> None:
        self.journals: list[JournalRecord] = []
        self.conversations: list[ConversationRecord] = []
        self.analyses: list[dict[str, Any]] = []
        self.daily: dict[date, DailyMoodRecord] = {}

    def rebuild_daily(self) -> DailyMoodRecord:
        record = aggregate_daily_mood(
            TEST_TIME.date(),
            self.analyses,
            updated_at=TEST_TIME,
        )
        self.daily[record.date] = record
        return record


class FlowJournalService:
    def __init__(self, store: FlowStore) -> None:
        self.store = store

    def create_journal(self, uid: str, text: str) -> JournalRecord:
        assert uid == "flow-user"
        record = JournalRecord(
            id=f"journal-{len(self.store.journals) + 1}",
            text=text,
            created_at=TEST_TIME,
        )
        self.store.journals.append(record)
        return record

    def list_journals(self, uid: str, limit: int) -> list[JournalRecord]:
        assert uid == "flow-user"
        return self.store.journals[-limit:][::-1]


class FlowConversationService:
    def __init__(self, store: FlowStore) -> None:
        self.store = store

    def create_conversation(
        self,
        uid: str,
        turns: list[ConversationTurn],
        transcript: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> ConversationRecord:
        assert uid == "flow-user"
        record = ConversationRecord(
            id=f"conversation-{len(self.store.conversations) + 1}",
            transcript=transcript,
            turns=turns,
            started_at=started_at,
            ended_at=ended_at,
            created_at=TEST_TIME,
        )
        self.store.conversations.append(record)
        return record

    def list_conversations(self, uid: str, limit: int) -> list[ConversationRecord]:
        assert uid == "flow-user"
        return self.store.conversations[-limit:][::-1]


class FlowAnalysisService:
    def __init__(self, store: FlowStore) -> None:
        self.store = store

    def analyze(
        self,
        uid: str,
        text: str,
        source: str,
        source_id: str | None,
    ) -> AnalysisResponse:
        assert uid == "flow-user"
        if source == "journal":
            emotions = {
                "joy": 0.6,
                "sadness": 0.1,
                "anger": 0.05,
                "fear": 0.05,
                "neutral": 0.2,
            }
            mood_score = 70
            dominant = "joy"
        else:
            emotions = {
                "joy": 0.1,
                "sadness": 0.5,
                "anger": 0.1,
                "fear": 0.2,
                "neutral": 0.1,
            }
            mood_score = 40
            dominant = "sadness"
        self.store.analyses.append(
            {
                "source": source,
                "sourceId": source_id,
                "moodScore": mood_score,
                "emotions": emotions,
                "createdAt": TEST_TIME,
            }
        )
        self.store.rebuild_daily()
        return AnalysisResponse(
            source=source,  # type: ignore[arg-type]
            source_id=source_id,
            original_text=text,
            language="en",
            language_confidence=0.99,
            anonymized_text=text.replace("private@example.com", "[EMAIL]"),
            translated_text=text.replace("private@example.com", "[EMAIL]"),
            translation_applied=False,
            pii_entities=[],
            analysis_id=f"analysis-{len(self.store.analyses)}",
            created_at=TEST_TIME,
            emotions=emotions,
            dominant_emotion=dominant,  # type: ignore[arg-type]
            mood_score=mood_score,
            confidence=max(emotions.values()),
        )


class FlowDailyMoodService:
    def __init__(self, store: FlowStore) -> None:
        self.store = store

    def get(self, uid: str, target_date: date) -> DailyMoodRecord:
        assert uid == "flow-user"
        return self.store.daily[target_date]

    def rebuild(self, uid: str, target_date: date) -> DailyMoodRecord:
        assert uid == "flow-user"
        assert target_date == TEST_TIME.date()
        return self.store.rebuild_daily()

    def list_recent(self, uid: str, days: int) -> list[DailyMoodRecord]:
        assert uid == "flow-user"
        assert days == 7
        return sorted(self.store.daily.values(), key=lambda item: item.date)


def flow_user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="flow-user", email="flow@example.com")


async def test_journal_and_voice_flow_reaches_daily_dashboard_record() -> None:
    store = FlowStore()
    app.dependency_overrides[get_current_user] = flow_user
    app.dependency_overrides[get_journal_service] = lambda: FlowJournalService(store)
    app.dependency_overrides[get_conversation_service] = lambda: FlowConversationService(store)
    app.dependency_overrides[get_analysis_service] = lambda: FlowAnalysisService(store)
    app.dependency_overrides[get_daily_mood_service] = lambda: FlowDailyMoodService(store)

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            journal = await client.post(
                "/api/journal", json={"text": "I felt hopeful today."}
            )
            assert journal.status_code == 201

            journal_analysis = await client.post(
                "/api/analyze",
                json={
                    "text": journal.json()["text"],
                    "source": "journal",
                    "source_id": journal.json()["id"],
                },
            )
            assert journal_analysis.status_code == 200

            conversation = await client.post(
                "/api/conversations",
                json={
                    "turns": [
                        {"role": "user", "text": "Work made me anxious."},
                        {"role": "assistant", "text": "What felt hardest?"},
                    ],
                    "started_at": "2026-09-20T11:55:00Z",
                    "ended_at": "2026-09-20T12:00:00Z",
                },
            )
            assert conversation.status_code == 201

            conversation_analysis = await client.post(
                "/api/analyze",
                json={
                    "text": "Work made me anxious.",
                    "source": "conversation",
                    "source_id": conversation.json()["id"],
                },
            )
            assert conversation_analysis.status_code == 200

            daily = await client.get("/api/mood/daily?date=2026-09-20")
            history = await client.get("/api/mood/daily/history?days=7")
    finally:
        app.dependency_overrides.clear()

    assert daily.status_code == 200
    assert daily.json()["mood_score"] == 55
    assert daily.json()["journal_count"] == 1
    assert daily.json()["conversation_count"] == 1
    assert daily.json()["analysis_count"] == 2
    assert history.status_code == 200
    assert history.json()["count"] == 1
    assert history.json()["items"][0]["mood_score"] == 55

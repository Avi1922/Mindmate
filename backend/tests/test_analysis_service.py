"""Analysis orchestration and privacy-safe persistence tests."""

from app.models.analysis import EmotionScores, TextProcessingResponse
from app.services.analysis_service import AnalysisService
from app.services.daily_mood_service import DailyMoodStorageError
from app.services.mood_service import MoodService


class StubTextProcessor:
    def process(self, text: str, source: str) -> TextProcessingResponse:
        assert text == "My email is private@example.com and I feel hopeful."
        return TextProcessingResponse(
            source=source,  # type: ignore[arg-type]
            original_text=text,
            language="en",
            language_confidence=0.99,
            anonymized_text="My email is [EMAIL] and I feel hopeful.",
            translated_text="My email is [EMAIL] and I feel hopeful.",
            translation_applied=False,
            pii_entities=[{"type": "EMAIL", "count": 1}],
        )


class StubEmotionService:
    def classify(self, text: str) -> tuple[EmotionScores, str, float]:
        assert text == "My email is [EMAIL] and I feel hopeful."
        scores = EmotionScores(
            joy=0.6,
            sadness=0.1,
            anger=0.05,
            fear=0.05,
            neutral=0.2,
        )
        return scores, "joy", 0.6


class FakeDocument:
    def __init__(self, document_id: str) -> None:
        self.id = document_id
        self.saved: dict[str, object] | None = None

    def collection(self, name: str) -> "FakeCollection":
        assert name == "analyses"
        return FakeCollection(self)

    def set(self, payload: dict[str, object]) -> None:
        self.saved = payload


class FakeCollection:
    def __init__(self, analysis_document: FakeDocument) -> None:
        self.analysis_document = analysis_document

    def document(self, document_id: str | None = None) -> FakeDocument:
        if document_id is not None:
            assert document_id == "user-123"
        return self.analysis_document


class FakeFirestore:
    def __init__(self, analysis_document: FakeDocument) -> None:
        self.analysis_document = analysis_document

    def collection(self, name: str) -> FakeCollection:
        assert name == "users"
        return FakeCollection(self.analysis_document)


class FakeFirebase:
    def __init__(self, analysis_document: FakeDocument) -> None:
        self.firestore = FakeFirestore(analysis_document)

    def get_firestore_client(self) -> FakeFirestore:
        return self.firestore


class StubDailyMoodService:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, object]] = []

    def rebuild(self, uid: str, target_date: object) -> None:
        self.calls.append((uid, target_date))
        if self.fail:
            raise DailyMoodStorageError("offline")


def test_analysis_persists_only_privacy_processed_text() -> None:
    document = FakeDocument("analysis-123")
    daily_mood = StubDailyMoodService()
    service = AnalysisService(
        text_processor=StubTextProcessor(),  # type: ignore[arg-type]
        emotion=StubEmotionService(),  # type: ignore[arg-type]
        mood=MoodService(),
        firebase=FakeFirebase(document),  # type: ignore[arg-type]
        daily_mood=daily_mood,  # type: ignore[arg-type]
    )

    result = service.analyze(
        uid="user-123",
        text="My email is private@example.com and I feel hopeful.",
        source="journal",
        source_id="journal-123",
    )

    assert result.analysis_id == "analysis-123"
    assert result.dominant_emotion == "joy"
    assert document.saved is not None
    assert document.saved["sourceId"] == "journal-123"
    assert document.saved["anonymizedText"] == "My email is [EMAIL] and I feel hopeful."
    assert document.saved["translatedText"] == "My email is [EMAIL] and I feel hopeful."
    assert "originalText" not in document.saved
    assert "private@example.com" not in str(document.saved)
    assert daily_mood.calls == [("user-123", result.created_at.date())]


def test_saved_analysis_survives_daily_aggregation_outage() -> None:
    document = FakeDocument("analysis-123")
    service = AnalysisService(
        text_processor=StubTextProcessor(),  # type: ignore[arg-type]
        emotion=StubEmotionService(),  # type: ignore[arg-type]
        mood=MoodService(),
        firebase=FakeFirebase(document),  # type: ignore[arg-type]
        daily_mood=StubDailyMoodService(fail=True),  # type: ignore[arg-type]
    )

    result = service.analyze(
        uid="user-123",
        text="My email is private@example.com and I feel hopeful.",
        source="journal",
        source_id="journal-123",
    )

    assert result.analysis_id == "analysis-123"
    assert document.saved is not None

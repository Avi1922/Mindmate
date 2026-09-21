"""Complete text, emotion, mood, and persistence orchestration."""

from datetime import datetime, timezone
from functools import lru_cache
import logging

from app.models.analysis import AnalysisResponse, AnalysisSource
from app.services.emotion_service import EmotionService, get_emotion_service
from app.services.daily_mood_service import (
    DailyMoodNotFoundError,
    DailyMoodService,
    DailyMoodStorageError,
    get_daily_mood_service,
)
from app.services.firebase_service import FirebaseService, get_firebase_service
from app.services.mood_service import MoodService
from app.services.text_processing_service import (
    TextProcessingService,
    get_text_processing_service,
)


class AnalysisStorageError(RuntimeError):
    """Raised when a completed analysis cannot be persisted."""


logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        text_processor: TextProcessingService,
        emotion: EmotionService,
        mood: MoodService,
        firebase: FirebaseService,
        daily_mood: DailyMoodService | None = None,
    ) -> None:
        self._text_processor = text_processor
        self._emotion = emotion
        self._mood = mood
        self._firebase = firebase
        self._daily_mood = daily_mood

    def analyze(
        self,
        uid: str,
        text: str,
        source: AnalysisSource,
        source_id: str | None,
    ) -> AnalysisResponse:
        processed = self._text_processor.process(text, source)
        emotions, dominant_emotion, confidence = self._emotion.classify(
            processed.translated_text
        )
        mood_score = self._mood.calculate(emotions)
        created_at = datetime.now(timezone.utc)

        try:
            document = (
                self._firebase.get_firestore_client()
                .collection("users")
                .document(uid)
                .collection("analyses")
                .document()
            )
            document.set(
                {
                    "source": source,
                    "sourceId": source_id,
                    "language": processed.language,
                    "languageConfidence": processed.language_confidence,
                    "anonymizedText": processed.anonymized_text,
                    "translatedText": processed.translated_text,
                    "translationApplied": processed.translation_applied,
                    "piiEntities": [
                        item.model_dump() for item in processed.pii_entities
                    ],
                    "emotions": emotions.model_dump(),
                    "dominantEmotion": dominant_emotion,
                    "moodScore": mood_score,
                    "confidence": confidence,
                    "createdAt": created_at,
                }
            )
        except Exception as exc:
            raise AnalysisStorageError("Analysis result could not be saved") from exc

        if self._daily_mood is not None:
            try:
                self._daily_mood.rebuild(uid, created_at.date())
            except (DailyMoodNotFoundError, DailyMoodStorageError):
                # The analysis is already safely stored. A user can retry the
                # deterministic rebuild endpoint without duplicating it.
                logger.warning("Daily mood aggregation failed after analysis storage")

        return AnalysisResponse(
            **processed.model_dump(),
            analysis_id=document.id,
            source_id=source_id,
            created_at=created_at,
            emotions=emotions,
            dominant_emotion=dominant_emotion,
            mood_score=mood_score,
            confidence=confidence,
        )


@lru_cache
def get_analysis_service() -> AnalysisService:
    return AnalysisService(
        text_processor=get_text_processing_service(),
        emotion=get_emotion_service(),
        mood=MoodService(),
        firebase=get_firebase_service(),
        daily_mood=get_daily_mood_service(),
    )

"""Retry an existing journal without creating another source or analysis."""

import hashlib
from threading import Lock

from google.cloud.firestore_v1.base_query import FieldFilter

from app.models.analysis import AnalysisResponse
from app.services.analysis_service import get_analysis_service
from app.services.firebase_service import get_firebase_service
from app.services.mood_service import read_signed_score

_locks = [Lock() for _ in range(64)]


class JournalMissing(RuntimeError):
    pass


def analyze_saved_journal(uid: str, journal_id: str) -> AnalysisResponse:
    digest = hashlib.sha256((uid + ":" + journal_id).encode()).hexdigest()
    with _locks[int(digest[:8], 16) % len(_locks)]:
        user = (
            get_firebase_service()
            .get_firestore_client()
            .collection("users")
            .document(uid)
        )
        snapshot = (
            user.collection("journals").document(journal_id).get(timeout=8, retry=None)
        )
        if not snapshot.exists:
            raise JournalMissing("Journal not found")
        text = (snapshot.to_dict() or {}).get("text", "")
        analyses = user.collection("analyses")
        existing = analyses.where(
            filter=FieldFilter("sourceId", "==", journal_id)
        ).stream(timeout=8, retry=None)
        for record in existing:
            data = record.to_dict() or {}
            if data.get("source") == "journal":
                return AnalysisResponse(
                    analysis_id=record.id,
                    source_id=journal_id,
                    source="journal",
                    original_text=text,
                    language=data["language"],
                    language_confidence=data["languageConfidence"],
                    anonymized_text=data["anonymizedText"],
                    translated_text=data["translatedText"],
                    translation_applied=data["translationApplied"],
                    pii_entities=data["piiEntities"],
                    created_at=data["createdAt"],
                    emotions=data["emotions"],
                    dominant_emotion=data["dominantEmotion"],
                    mood_score=read_signed_score(data),
                    confidence=data["confidence"],
                )
        return get_analysis_service().analyze(
            uid, text, "journal", journal_id, analysis_id="journal-" + digest
        )

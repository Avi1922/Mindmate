"""Retry returns stored results and cannot read another user's journal."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.services import journal_analysis_service as service


def test_retry_reuses_saved_result(monkeypatch):
    data = {
        "source": "journal",
        "language": "en",
        "languageConfidence": 1,
        "anonymizedText": "Calm",
        "translatedText": "Calm",
        "translationApplied": False,
        "piiEntities": [],
        "createdAt": datetime.now(UTC),
        "emotions": {
            "joy": 0.5,
            "sadness": 0.1,
            "anger": 0.1,
            "fear": 0.1,
            "neutral": 0.2,
        },
        "dominantEmotion": "joy",
        "moodScore": 62,
        "confidence": 0.5,
    }
    existing = SimpleNamespace(id="already-analyzed", to_dict=lambda: data)
    journals = Mock()
    journals.document.return_value.get.return_value = SimpleNamespace(
        exists=True, to_dict=lambda: {"text": "Calm"}
    )
    analyses = Mock()
    analyses.where.return_value.stream.return_value = [existing]
    owner = Mock()
    owner.collection.side_effect = lambda name: (
        journals if name == "journals" else analyses
    )
    db = Mock()
    db.collection.return_value.document.return_value = owner
    monkeypatch.setattr(
        service,
        "get_firebase_service",
        lambda: SimpleNamespace(get_firestore_client=lambda: db),
    )
    analyzer = Mock()
    monkeypatch.setattr(service, "get_analysis_service", lambda: analyzer)
    assert (
        service.analyze_saved_journal("owner", "journal-one").analysis_id
        == "already-analyzed"
    )
    analyzer.analyze.assert_not_called()
    db.collection.return_value.document.assert_called_once_with("owner")


def test_retry_rejects_missing_owner_journal(monkeypatch):
    db = Mock()
    db.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = SimpleNamespace(
        exists=False
    )
    monkeypatch.setattr(
        service,
        "get_firebase_service",
        lambda: SimpleNamespace(get_firestore_client=lambda: db),
    )
    with pytest.raises(service.JournalMissing):
        service.analyze_saved_journal("owner", "another-users-entry")

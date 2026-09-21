"""Protected text-analysis API tests."""

from datetime import UTC, datetime
from typing import Any

import pytest
from app.main import app
from app.models.analysis import AnalysisResponse
from app.models.auth import AuthenticatedUser
from app.services.analysis_service import get_analysis_service
from app.services.translation_service import TranslationError
from app.utils.auth import get_current_user
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.asyncio


class StubProcessor:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def analyze(
        self,
        uid: str,
        text: str,
        source: str,
        source_id: str | None,
    ) -> AnalysisResponse:
        if self.error:
            raise self.error
        assert uid == "user-123"
        return AnalysisResponse(
            source=source,  # type: ignore[arg-type]
            source_id=source_id,
            original_text=text,
            language="en",
            language_confidence=0.99,
            anonymized_text="Contact [EMAIL]. I felt hopeful.",
            translated_text="Contact [EMAIL]. I felt hopeful.",
            translation_applied=False,
            pii_entities=[{"type": "EMAIL", "count": 1}],
            analysis_id="analysis-1",
            created_at=datetime(2026, 9, 20, 12, 0, tzinfo=UTC),
            emotions={
                "joy": 0.55,
                "sadness": 0.1,
                "anger": 0.05,
                "fear": 0.05,
                "neutral": 0.25,
            },
            dominant_emotion="joy",
            mood_score=71,
            confidence=0.55,
        )


def override_user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="user-123", email="person@example.com")


async def request_analysis(
    payload: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/analyze", json=payload)
    return response.status_code, response.json()


async def test_analyze_returns_phase_seven_response() -> None:
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_analysis_service] = lambda: StubProcessor()
    try:
        status_code, body = await request_analysis(
            {
                "text": "Contact me at private@example.com. I felt hopeful.",
                "source": "journal",
                "source_id": "journal-1",
            }
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 200
    assert body["language"] == "en"
    assert body["anonymized_text"] == "Contact [EMAIL]. I felt hopeful."
    assert body["analysis_id"] == "analysis-1"
    assert body["source_id"] == "journal-1"
    assert body["emotions"]["joy"] == 0.55
    assert body["dominant_emotion"] == "joy"
    assert body["mood_score"] == 71


async def test_analyze_requires_authentication() -> None:
    status_code, body = await request_analysis(
        {"text": "I felt hopeful.", "source": "journal"}
    )

    assert status_code == 401
    assert body == {"detail": "Authentication required"}


async def test_analyze_rejects_blank_text() -> None:
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_analysis_service] = lambda: StubProcessor()
    try:
        status_code, body = await request_analysis({"text": "   ", "source": "journal"})
    finally:
        app.dependency_overrides.clear()

    assert status_code == 422
    assert body["detail"]


async def test_analyze_handles_translation_outage() -> None:
    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_analysis_service] = lambda: StubProcessor(
        TranslationError("offline")
    )
    try:
        status_code, body = await request_analysis(
            {"text": "Aaj din kharab tha.", "source": "journal"}
        )
    finally:
        app.dependency_overrides.clear()

    assert status_code == 503
    assert body == {"detail": "Translation is temporarily unavailable"}

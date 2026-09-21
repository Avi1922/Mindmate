"""Structured emotion parsing, normalization, and fallback tests."""

from types import SimpleNamespace

import pytest
from app.models.analysis import EmotionScores
from app.services import emotion_service as emotion_module
from app.services.emotion_service import EmotionAnalysisError, EmotionService
from app.utils.config import Settings
from google.genai import errors
from pydantic import SecretStr


def test_parses_json_emotion_response() -> None:
    response = SimpleNamespace(
        parsed=None,
        text=('{"joy":0.1,"sadness":0.55,"anger":0.15,"fear":0.15,"neutral":0.05}'),
    )

    result = EmotionService._parse_response(response)

    assert result.sadness == 0.55
    assert sum(result.model_dump().values()) == pytest.approx(1.0)


def test_normalizes_model_scores() -> None:
    scores = EmotionScores(
        joy=0.2,
        sadness=0.4,
        anger=0.2,
        fear=0.1,
        neutral=0.1,
    )

    result = EmotionService._normalize(scores)

    assert sum(result.model_dump().values()) == pytest.approx(1.0)


def test_rejects_zero_probability_mass() -> None:
    scores = EmotionScores(joy=0, sadness=0, anger=0, fear=0, neutral=0)

    with pytest.raises(EmotionAnalysisError):
        EmotionService._normalize(scores)


class FakeModels:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def generate_content(self, *, model: str, **_: object) -> SimpleNamespace:
        self.calls.append(model)
        if model == "gemini-3.8-flash":
            raise errors.ServerError(
                503,
                {"error": {"code": 503, "status": "UNAVAILABLE"}},
            )
        return SimpleNamespace(
            parsed=EmotionScores(
                joy=0.6,
                sadness=0.1,
                anger=0.05,
                fear=0.05,
                neutral=0.2,
            ),
            text=None,
        )


class FakeClient:
    def __init__(self) -> None:
        self.models = FakeModels()


def test_emotion_classification_falls_back_on_transient_error(monkeypatch) -> None:
    client = FakeClient()
    monkeypatch.setattr(emotion_module.genai, "Client", lambda **_: client)
    service = EmotionService(
        Settings(
            gemini_api_key=SecretStr("test-key"),
            gemini_text_model="gemini-3.8-flash",
            gemini_text_fallback_model="gemini-3.5-flash-lite",
        )
    )

    emotions, dominant, confidence = service.classify("I feel hopeful.")

    assert dominant == "joy"
    assert confidence == pytest.approx(0.6)
    assert emotions.joy == pytest.approx(0.6)
    assert client.models.calls == ["gemini-3.8-flash", "gemini-3.5-flash-lite"]

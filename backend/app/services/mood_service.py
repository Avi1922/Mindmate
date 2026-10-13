"""Explainable signed mood estimates and legacy score compatibility."""

from collections.abc import Mapping
from typing import Any

from app.models.analysis import EmotionScores

SCORE_SCALE = "signed-v1"


def read_signed_score(data: Mapping[str, Any]) -> int:
    """Convert unversioned 0..100 records without rewriting historical data."""
    score = float(data["moodScore"])
    if data.get("scoreScale") == SCORE_SCALE:
        if not -100 <= score <= 100:
            raise ValueError("Invalid signed mood score")
        return round(score)
    if not 0 <= score <= 100:
        raise ValueError("Invalid legacy mood score")
    return round(2 * score - 100)


class MoodService:
    """100 * (joy - .8*sadness - .9*anger - .7*fear); neutral is zero."""

    def calculate(self, emotions: EmotionScores) -> int:
        valence = (
            emotions.joy
            - 0.8 * emotions.sadness
            - 0.9 * emotions.anger
            - 0.7 * emotions.fear
        )
        return round(max(-100, min(100, 100 * valence)))

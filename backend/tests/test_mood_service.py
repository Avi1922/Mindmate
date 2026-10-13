"""Explainable mood-score calculation tests."""

import pytest
from app.models.analysis import EmotionScores
from app.services.mood_service import MoodService


@pytest.mark.parametrize(
    ("emotions", "expected"),
    [
        ({"joy": 1, "sadness": 0, "anger": 0, "fear": 0, "neutral": 0}, 100),
        ({"joy": 0, "sadness": 1, "anger": 0, "fear": 0, "neutral": 0}, -80),
        ({"joy": 0, "sadness": 0, "anger": 1, "fear": 0, "neutral": 0}, -90),
        ({"joy": 0, "sadness": 0, "anger": 0, "fear": 1, "neutral": 0}, -70),
        ({"joy": 0, "sadness": 0, "anger": 0, "fear": 0, "neutral": 1}, 0),
    ],
)
def test_mood_score_anchor_points(
    emotions: dict[str, float],
    expected: int,
) -> None:
    assert MoodService().calculate(EmotionScores(**emotions)) == expected


def test_mood_score_is_clamped_to_application_range() -> None:
    emotions = EmotionScores(
        joy=0,
        sadness=1,
        anger=1,
        fear=1,
        neutral=0,
    )

    assert MoodService().calculate(emotions) == -100


def test_legacy_score_conversion_is_applied_exactly_once() -> None:
    from app.services.mood_service import read_signed_score

    assert read_signed_score({"moodScore": 50}) == 0
    assert read_signed_score({"moodScore": 10}) == -80
    assert read_signed_score({"moodScore": 90}) == 80
    assert read_signed_score({"moodScore": 10, "scoreScale": "signed-v1"}) == 10
    assert read_signed_score({"moodScore": -80, "scoreScale": "signed-v1"}) == -80

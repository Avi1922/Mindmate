"""Explainable application-level mood estimate calculation."""

from app.models.analysis import EmotionScores


class MoodService:
    """Convert emotion probabilities into a replaceable 0–100 estimate.

    Formula:
      50 + 50 * (joy - 0.8*sadness - 0.9*anger - 0.7*fear)

    Neutral leaves the baseline at 50. The result is rounded and clamped.
    """

    def calculate(self, emotions: EmotionScores) -> int:
        valence = (
            emotions.joy
            - 0.8 * emotions.sadness
            - 0.9 * emotions.anger
            - 0.7 * emotions.fear
        )
        raw_score = 50 + 50 * valence
        return round(max(0, min(100, raw_score)))

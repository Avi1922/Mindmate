"""Stored, deterministic daily encouragement; no provider requests."""

MOOD_MESSAGES = (
    (81, "Your mood is great today."),
    (40, "There is positive energy in your day. Enjoy a small moment that feels good."),
    (10, "Your day has some encouraging moments. Keep making time for yourself."),
    (
        -10,
        "Your mood feels fairly balanced today. A small check-in can help you reflect.",
    ),
    (-40, "Today may feel a little difficult. Give yourself room for a gentle pause."),
    (
        -80,
        "Today feels heavy. Take one small step and consider talking to someone you trust.",
    ),
    (
        -100,
        "You deserve care on difficult days. Slow down and reach out for support if you need it.",
    ),
)


def mood_message(score: int) -> str:
    for threshold, message in MOOD_MESSAGES:
        if score >= threshold:
            return message
    return MOOD_MESSAGES[-1][1]

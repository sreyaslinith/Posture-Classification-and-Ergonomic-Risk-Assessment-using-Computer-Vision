"""
Wellness score calculator.
Combines posture, blink health, yawn frequency, and session consistency.
"""

# Weights (must sum to 1.0)
WEIGHT_POSTURE = 0.40
WEIGHT_BLINK = 0.30
WEIGHT_YAWN = 0.20
WEIGHT_CONSISTENCY = 0.10

RECOMMENDATIONS = [
    "Sit upright with shoulders relaxed.",
    "Take eye breaks every 20 minutes (20-20-20 rule).",
    "Stretch neck and shoulders every hour.",
    "Drink water regularly to stay hydrated.",
    "Get adequate sleep (7-9 hours) for better focus.",
]


def _blink_score(blink_rate: float) -> float:
    """
    Score blink health (0-100).
    Healthy range: 10-20 blinks/min.
    """
    if blink_rate <= 0:
        return 50.0
    if 10 <= blink_rate <= 20:
        return 100.0
    if blink_rate < 10:
        return max(20.0, 100.0 - (10 - blink_rate) * 8)
    if blink_rate <= 30:
        return max(60.0, 100.0 - (blink_rate - 20) * 3)
    return max(20.0, 100.0 - (blink_rate - 30) * 5)


def _yawn_score(yawns_per_hour: float) -> float:
    """Score yawn frequency (0-100). Normal: 0-2/hour."""
    if yawns_per_hour <= 2:
        return 100.0
    if yawns_per_hour <= 5:
        return 75.0
    return max(20.0, 100.0 - (yawns_per_hour - 5) * 10)


def _consistency_score(records_count: int, session_minutes: float) -> float:
    """
    Score session consistency based on data coverage.
    Expects roughly 1 record per second.
    """
    if session_minutes <= 0:
        return 50.0
    expected = session_minutes * 60
    ratio = min(records_count / max(expected, 1), 1.0)
    return round(ratio * 100, 1)


def wellness_label(score: float) -> str:
    """Map wellness score to health status label."""
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Average"
    return "Poor"


def calculate_wellness(
    posture_score: float,
    blink_rate: float,
    yawns_per_hour: float,
    records_count: int = 0,
    session_minutes: float = 0.0,
) -> dict:
    """
    Compute composite wellness score.

    Returns dict with wellness_score, label, component scores, recommendations.
    """
    blink = _blink_score(blink_rate)
    yawn = _yawn_score(yawns_per_hour)
    consistency = _consistency_score(records_count, session_minutes)

    total = (
        posture_score * WEIGHT_POSTURE
        + blink * WEIGHT_BLINK
        + yawn * WEIGHT_YAWN
        + consistency * WEIGHT_CONSISTENCY
    )
    total = round(max(0, min(100, total)), 1)

    recs = list(RECOMMENDATIONS)
    if posture_score < 70:
        recs.insert(0, "Improve posture — align ears over shoulders.")
    if blink_rate < 10:
        recs.insert(0, "Blink more often to reduce eye strain.")
    if yawns_per_hour > 5:
        recs.insert(0, "Consider a short break — signs of fatigue detected.")

    return {
        "wellness_score": total,
        "label": wellness_label(total),
        "posture_component": round(posture_score, 1),
        "blink_component": round(blink, 1),
        "yawn_component": round(yawn, 1),
        "consistency_component": round(consistency, 1),
        "recommendations": recs,
    }

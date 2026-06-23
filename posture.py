"""
Posture analysis: angle calculation and classification.
Measures the ear → shoulder → hip angle to assess sitting posture.
"""

from typing import Optional

import numpy as np

from utils import (
    calculate_angle,
    posture_from_angle,
    posture_color,
    posture_score,
    POSTURE_GOOD,
    POSTURE_OKAY,
    POSTURE_BAD,
)


class PostureAnalyzer:
    """Computes posture angle and label from pose landmark points."""

    def analyze(self, points: Optional[dict]) -> Optional[dict]:
        """
        Analyze posture from ear/shoulder/hip landmark dict.

        Args:
            points: Dict with 'ear', 'shoulder', 'hip' numpy arrays.

        Returns:
            Dict with angle, posture label, colour, and score; or None.
        """
        if points is None:
            return None

        try:
            angle = calculate_angle(
                points["ear"],
                points["shoulder"],
                points["hip"],
            )
            posture = posture_from_angle(angle)
            return {
                "angle": angle,
                "posture": posture,
                "color": posture_color(posture),
                "score": posture_score(posture),
                "label_display": _display_label(posture),
            }
        except (KeyError, TypeError, ValueError) as exc:
            print(f"[posture] Analysis error: {exc}")
            return None


def _display_label(posture: str) -> str:
    """Return uppercase display string for UI overlay."""
    labels = {
        POSTURE_GOOD: "GOOD POSTURE",
        POSTURE_OKAY: "OKAY POSTURE",
        POSTURE_BAD: "BAD POSTURE",
    }
    return labels.get(posture, "UNKNOWN")

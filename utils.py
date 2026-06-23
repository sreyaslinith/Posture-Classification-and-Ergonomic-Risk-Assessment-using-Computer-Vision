"""
Utility helpers for ErgoVisionAI.
Handles FPS tracking, CSV export, time formatting, and shared constants.
"""

import os
import csv
import time
from datetime import datetime
from typing import Optional

import numpy as np

# ---------------------------------------------------------------------------
# Paths (relative to this package directory)
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "posture.db")
CSV_PATH = os.path.join(BASE_DIR, "posture_history.csv")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# ---------------------------------------------------------------------------
# Posture thresholds (degrees)
# ---------------------------------------------------------------------------
GOOD_THRESHOLD = 165
OKAY_THRESHOLD = 150

# Posture labels
POSTURE_GOOD = "Good"
POSTURE_OKAY = "Okay"
POSTURE_BAD = "Bad"

# UI colours (BGR for OpenCV)
COLOR_GOOD = (0, 200, 0)
COLOR_OKAY = (0, 200, 255)
COLOR_BAD = (0, 0, 255)
COLOR_TEXT = (220, 220, 220)
COLOR_ACCENT = (255, 180, 50)
COLOR_BG_DARK = (30, 30, 30)


class FPSTracker:
    """Simple rolling FPS calculator for real-time display."""

    def __init__(self, window_size: int = 30):
        self._times: list[float] = []
        self._window_size = window_size

    def tick(self) -> float:
        """Record a frame timestamp and return current FPS."""
        now = time.time()
        self._times.append(now)
        if len(self._times) > self._window_size:
            self._times.pop(0)
        if len(self._times) < 2:
            return 0.0
        elapsed = self._times[-1] - self._times[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._times) - 1) / elapsed


def calculate_angle(
    point_a: np.ndarray,
    point_b: np.ndarray,
    point_c: np.ndarray,
) -> float:
    """
    Calculate the angle at point_b formed by vectors B->A and B->C.

    Args:
        point_a: First endpoint (e.g. ear).
        point_b: Vertex point (e.g. shoulder).
        point_c: Second endpoint (e.g. hip).

    Returns:
        Angle in degrees (0-180).
    """
    ba = point_a - point_b
    bc = point_c - point_b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba < 1e-6 or norm_bc < 1e-6:
        return 0.0

    cosine = np.dot(ba, bc) / (norm_ba * norm_bc)
    cosine = np.clip(cosine, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def posture_from_angle(angle: float) -> str:
    """Classify posture label from neck/spine angle."""
    if angle > GOOD_THRESHOLD:
        return POSTURE_GOOD
    if angle >= OKAY_THRESHOLD:
        return POSTURE_OKAY
    return POSTURE_BAD


def posture_color(posture: str) -> tuple:
    """Return BGR colour for a posture label."""
    if posture == POSTURE_GOOD:
        return COLOR_GOOD
    if posture == POSTURE_OKAY:
        return COLOR_OKAY
    return COLOR_BAD


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def current_timestamp() -> str:
    """Return current datetime as ISO string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def export_to_csv(
    timestamp: str,
    angle: float,
    posture: str,
    csv_path: str = CSV_PATH,
) -> None:
    """
    Append a single posture record to the CSV history file.
    Creates the file with headers if it does not exist.
    """
    file_exists = os.path.isfile(csv_path)
    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "angle", "posture"])
            writer.writerow([timestamp, round(angle, 2), posture])
    except OSError as exc:
        print(f"[utils] CSV export error: {exc}")


def posture_score(posture: str) -> int:
    """Map posture label to a numeric score (0-100)."""
    scores = {POSTURE_GOOD: 100, POSTURE_OKAY: 65, POSTURE_BAD: 25}
    return scores.get(posture, 0)

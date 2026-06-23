"""
Voice and visual alerts for sustained bad posture.
Uses pyttsx3 for text-to-speech; repeats every 10 seconds while bad posture persists.
"""

import threading
import time

import cv2

from utils import POSTURE_BAD, COLOR_BAD, COLOR_ACCENT, COLOR_TEXT

# Seconds of bad posture before first alert
BAD_POSTURE_THRESHOLD_SEC = 10
# Minimum interval between repeated voice alerts
ALERT_REPEAT_INTERVAL_SEC = 10


class PostureAlertManager:
    """Tracks bad-posture duration and triggers voice/visual alerts."""

    def __init__(self):
        self._bad_start: float | None = None
        self._last_alert_time: float = 0.0
        self._bad_posture_count: int = 0
        self._tts_engine = None
        self._tts_lock = threading.Lock()
        self._init_tts()

    def _init_tts(self) -> None:
        """Initialise pyttsx3 engine (gracefully skip if unavailable)."""
        try:
            import pyttsx3

            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate", 150)
            self._tts_engine.setProperty("volume", 1.0)
        except Exception as exc:
            print(f"[alerts] TTS init failed (voice alerts disabled): {exc}")
            self._tts_engine = None

    def update(self, posture: str | None) -> bool:
        """
        Update alert state for the current frame.

        Args:
            posture: Current posture label or None if undetected.

        Returns:
            True if a visual alert should be shown this frame.
        """
        now = time.time()

        if posture != POSTURE_BAD:
            self._bad_start = None
            return False

        if self._bad_start is None:
            self._bad_start = now

        bad_duration = now - self._bad_start
        if bad_duration < BAD_POSTURE_THRESHOLD_SEC:
            return False

        # Trigger voice alert at most once every ALERT_REPEAT_INTERVAL_SEC
        if now - self._last_alert_time >= ALERT_REPEAT_INTERVAL_SEC:
            self._last_alert_time = now
            self._bad_posture_count += 1
            self._speak_async("Please sit straight. Adjust your posture.")

        return True

    def _speak_async(self, message: str) -> None:
        """Speak message in a background thread to avoid blocking video."""
        if self._tts_engine is None:
            return

        def _speak():
            with self._tts_lock:
                try:
                    self._tts_engine.say(message)
                    self._tts_engine.runAndWait()
                except Exception as exc:
                    print(f"[alerts] TTS error: {exc}")

        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()

    @property
    def bad_posture_count(self) -> int:
        """Number of bad-posture alert events triggered."""
        return self._bad_posture_count

    def draw_alert_overlay(self, frame, show_alert: bool) -> None:
        """Draw warning banner on frame when bad posture alert is active."""
        if not show_alert:
            return

        h, w = frame.shape[:2]
        banner_h = 60
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - banner_h), (w, h), (0, 0, 80), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        text = "Sit Straight"
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(text, font, 1.0, 2)[0]
        text_x = (w - text_size[0]) // 2
        text_y = h - 20
        cv2.putText(
            frame,
            text,
            (text_x, text_y),
            font,
            1.0,
            COLOR_BAD,
            2,
            cv2.LINE_AA,
        )

    def release(self) -> None:
        """Clean up TTS engine."""
        if self._tts_engine is not None:
            try:
                self._tts_engine.stop()
            except Exception:
                pass

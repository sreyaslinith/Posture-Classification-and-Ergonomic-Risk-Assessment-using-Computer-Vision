"""
Blink rate detection using MediaPipe Face Landmarker.
Computes Eye Aspect Ratio (EAR) and blinks per minute.
"""

import os
import time
import urllib.request
from collections import deque

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
FACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_landmarker.task")
FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)

# EAR landmark indices (MediaPipe Face Mesh)
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

EAR_THRESHOLD = 0.21
BLINK_COOLDOWN_SEC = 0.3


def _ensure_face_model() -> str:
    if os.path.isfile(FACE_MODEL_PATH):
        return FACE_MODEL_PATH
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("[blink] Downloading face model...")
    urllib.request.urlretrieve(FACE_MODEL_URL, FACE_MODEL_PATH)
    return FACE_MODEL_PATH


def _ear(landmarks, indices, w: int, h: int) -> float:
    """Compute Eye Aspect Ratio for one eye."""
    pts = [np.array([landmarks[i].x * w, landmarks[i].y * h]) for i in indices]
    vertical_1 = np.linalg.norm(pts[1] - pts[5])
    vertical_2 = np.linalg.norm(pts[2] - pts[4])
    horizontal = np.linalg.norm(pts[0] - pts[3])
    if horizontal < 1e-6:
        return 0.3
    return (vertical_1 + vertical_2) / (2.0 * horizontal)


class BlinkDetector:
    """Tracks blinks and blink rate per minute."""

    def __init__(self):
        model_path = _ensure_face_model()
        options = vision.FaceLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        self._ts_ms = 0

        self.total_blinks = 0
        self._was_closed = False
        self._last_blink_time = 0.0
        self._blink_times: deque = deque(maxlen=300)
        self._session_start = time.time()

    def process(self, frame: np.ndarray) -> dict:
        """
        Detect blinks in a BGR frame.

        Returns dict with blink_count, blink_rate, ear, health_status.
        """
        h, w = frame.shape[:2]
        result = {
            "blink_count": self.total_blinks,
            "blink_rate": 0.0,
            "ear": 0.0,
            "health_status": "No Face Detected",
        }

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._ts_ms = int(time.time() * 1000)
        detection = self._landmarker.detect_for_video(mp_image, self._ts_ms)

        if not detection.face_landmarks:
            return result

        lms = detection.face_landmarks[0]
        left_ear = _ear(lms, LEFT_EYE, w, h)
        right_ear = _ear(lms, RIGHT_EYE, w, h)
        avg_ear = (left_ear + right_ear) / 2.0
        result["ear"] = round(avg_ear, 3)

        # Blink = EAR drops below threshold then reopens
        is_closed = avg_ear < EAR_THRESHOLD
        now = time.time()
        if is_closed and not self._was_closed:
            if now - self._last_blink_time > BLINK_COOLDOWN_SEC:
                self.total_blinks += 1
                self._blink_times.append(now)
                self._last_blink_time = now
        self._was_closed = is_closed

        # Blink rate per minute (rolling 60 s window)
        cutoff = now - 60.0
        recent = [t for t in self._blink_times if t >= cutoff]
        result["blink_rate"] = round(len(recent), 1)
        result["blink_count"] = self.total_blinks

        rate = result["blink_rate"]
        if rate < 10:
            result["health_status"] = "Eye Strain Risk"
        elif rate <= 20:
            result["health_status"] = "Healthy"
        elif rate <= 30:
            result["health_status"] = "Healthy"
        else:
            result["health_status"] = "Fatigue Indication"

        return result

    def get_average_rate(self) -> float:
        """Average blinks per minute over the session."""
        elapsed_min = max((time.time() - self._session_start) / 60.0, 0.01)
        return round(self.total_blinks / elapsed_min, 1)

    def reset(self):
        self.total_blinks = 0
        self._was_closed = False
        self._blink_times.clear()
        self._session_start = time.time()

    def close(self):
        try:
            self._landmarker.close()
        except Exception:
            pass

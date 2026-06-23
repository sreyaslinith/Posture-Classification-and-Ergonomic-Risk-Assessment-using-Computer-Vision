"""
Yawning detection using mouth opening ratio from Face Landmarker.
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
FACE_MODEL_PATH = os.path.join(MODELS_DIR, "face_landmarker.task")
FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)

# Mouth landmarks: upper lip, lower lip, left corner, right corner
MOUTH_TOP = 13
MOUTH_BOTTOM = 14
MOUTH_LEFT = 61
MOUTH_RIGHT = 291

MAR_YAWN_THRESHOLD = 0.55
YAWN_MIN_FRAMES = 8
YAWN_COOLDOWN_SEC = 2.0


def _ensure_face_model() -> str:
    if os.path.isfile(FACE_MODEL_PATH):
        return FACE_MODEL_PATH
    os.makedirs(MODELS_DIR, exist_ok=True)
    print("[yawn] Downloading face model...")
    urllib.request.urlretrieve(FACE_MODEL_URL, FACE_MODEL_PATH)
    return FACE_MODEL_PATH


def _mouth_aspect_ratio(landmarks, w: int, h: int) -> float:
    """Mouth opening ratio = vertical / horizontal distance."""
    top = np.array([landmarks[MOUTH_TOP].x * w, landmarks[MOUTH_TOP].y * h])
    bottom = np.array([landmarks[MOUTH_BOTTOM].x * w, landmarks[MOUTH_BOTTOM].y * h])
    left = np.array([landmarks[MOUTH_LEFT].x * w, landmarks[MOUTH_LEFT].y * h])
    right = np.array([landmarks[MOUTH_RIGHT].x * w, landmarks[MOUTH_RIGHT].y * h])
    vertical = np.linalg.norm(top - bottom)
    horizontal = np.linalg.norm(left - right)
    if horizontal < 1e-6:
        return 0.0
    return vertical / horizontal


class YawnDetector:
    """Detects yawns via sustained mouth opening."""

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

        self.total_yawns = 0
        self._open_frames = 0
        self._last_yawn_time = 0.0
        self._yawn_times: deque = deque(maxlen=300)
        self._session_start = time.time()

    def process(self, frame: np.ndarray) -> dict:
        """Detect yawns in a BGR frame."""
        h, w = frame.shape[:2]
        result = {
            "yawn_count": self.total_yawns,
            "yawns_per_minute": 0.0,
            "mar": 0.0,
            "health_status": "Normal",
        }

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._ts_ms = int(time.time() * 1000)
        detection = self._landmarker.detect_for_video(mp_image, self._ts_ms)

        if not detection.face_landmarks:
            self._open_frames = 0
            return result

        lms = detection.face_landmarks[0]
        mar = _mouth_aspect_ratio(lms, w, h)
        result["mar"] = round(mar, 3)

        if mar > MAR_YAWN_THRESHOLD:
            self._open_frames += 1
        else:
            if self._open_frames >= YAWN_MIN_FRAMES:
                now = time.time()
                if now - self._last_yawn_time > YAWN_COOLDOWN_SEC:
                    self.total_yawns += 1
                    self._yawn_times.append(now)
                    self._last_yawn_time = now
            self._open_frames = 0

        now = time.time()
        cutoff = now - 60.0
        recent = [t for t in self._yawn_times if t >= cutoff]
        result["yawns_per_minute"] = round(len(recent), 2)
        result["yawn_count"] = self.total_yawns

        # Health: convert to per hour estimate
        elapsed_hours = max((now - self._session_start) / 3600.0, 1 / 60)
        yawns_per_hour = self.total_yawns / elapsed_hours
        if yawns_per_hour <= 2:
            result["health_status"] = "Normal"
        elif yawns_per_hour <= 5:
            result["health_status"] = "Normal"
        else:
            result["health_status"] = "Fatigue Warning"

        return result

    def get_yawns_per_hour(self) -> float:
        elapsed_hours = max((time.time() - self._session_start) / 3600.0, 1 / 60)
        return round(self.total_yawns / elapsed_hours, 1)

    def reset(self):
        self.total_yawns = 0
        self._open_frames = 0
        self._yawn_times.clear()
        self._session_start = time.time()

    def close(self):
        try:
            self._landmarker.close()
        except Exception:
            pass

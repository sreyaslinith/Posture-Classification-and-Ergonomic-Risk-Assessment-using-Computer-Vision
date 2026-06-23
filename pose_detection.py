"""
MediaPipe Pose detection and skeleton rendering.
Uses the MediaPipe Tasks API (compatible with mediapipe >= 0.10.30).
Extracts key landmarks: nose, ears, shoulders, and hips.
"""

import os
import time
import urllib.request
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import drawing_utils, pose_landmarker

from utils import ASSETS_DIR

# MediaPipe landmark indices used for posture analysis
LANDMARK_NOSE = 0
LANDMARK_LEFT_EAR = 7
LANDMARK_RIGHT_EAR = 8
LANDMARK_LEFT_SHOULDER = 11
LANDMARK_RIGHT_SHOULDER = 12
LANDMARK_LEFT_HIP = 23
LANDMARK_RIGHT_HIP = 24

# Model file (downloaded automatically on first run)
MODEL_FILENAME = "pose_landmarker_lite.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
MODEL_PATH = os.path.join(ASSETS_DIR, MODEL_FILENAME)


def _ensure_model() -> str:
    """Download the pose landmarker model if not already present."""
    if os.path.isfile(MODEL_PATH):
        return MODEL_PATH

    os.makedirs(ASSETS_DIR, exist_ok=True)
    print(f"[pose_detection] Downloading pose model to {MODEL_PATH} ...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[pose_detection] Model download complete.")
    except Exception as exc:
        raise RuntimeError(
            f"Could not download pose model. Check your internet connection.\n{exc}"
        ) from exc
    return MODEL_PATH


class PoseDetector:
    """Wraps MediaPipe PoseLandmarker for landmark detection and skeleton drawing."""

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        model_path = _ensure_model()

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker = vision.PoseLandmarker.create_from_options(options)
        self._frame_timestamp_ms = 0

        self._landmark_style = drawing_utils.DrawingSpec(
            color=(50, 200, 255), thickness=2, circle_radius=4
        )
        self._connection_style = drawing_utils.DrawingSpec(
            color=(255, 180, 50), thickness=2
        )

    def process(self, frame: np.ndarray):
        """
        Run pose estimation on a BGR frame.

        Returns:
            PoseLandmarkerResult (or None on failure).
        """
        if frame is None or frame.size == 0:
            return None
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            self._frame_timestamp_ms = int(time.time() * 1000)
            results = self._landmarker.detect_for_video(
                mp_image, self._frame_timestamp_ms
            )
            return results
        except Exception as exc:
            print(f"[pose_detection] Processing error: {exc}")
            return None

    def draw_skeleton(self, frame: np.ndarray, results) -> np.ndarray:
        """Draw pose landmarks and connections on the frame."""
        if results is None or not results.pose_landmarks:
            return frame
        try:
            drawing_utils.draw_landmarks(
                frame,
                results.pose_landmarks[0],
                pose_landmarker.PoseLandmarksConnections.POSE_LANDMARKS,
                self._landmark_style,
                self._connection_style,
            )
        except Exception as exc:
            print(f"[pose_detection] Draw error: {exc}")
        return frame

    def get_landmark_point(
        self,
        results,
        landmark_idx: int,
        frame_width: int,
        frame_height: int,
    ) -> Optional[np.ndarray]:
        """
        Convert a normalised landmark to pixel coordinates [x, y].

        Returns None if landmark is not visible.
        """
        if results is None or not results.pose_landmarks:
            return None
        try:
            landmarks = results.pose_landmarks[0]
            if landmark_idx >= len(landmarks):
                return None
            lm = landmarks[landmark_idx]
            visibility = getattr(lm, "visibility", 1.0)
            if visibility is not None and visibility < 0.5:
                return None
            return np.array([lm.x * frame_width, lm.y * frame_height])
        except (IndexError, AttributeError):
            return None

    def get_posture_points(
        self,
        results,
        frame_width: int,
        frame_height: int,
    ) -> Optional[dict]:
        """
        Extract averaged ear, shoulder, and hip points for angle calculation.

        Returns dict with keys 'ear', 'shoulder', 'hip' or None if incomplete.
        """
        left_ear = self.get_landmark_point(
            results, LANDMARK_LEFT_EAR, frame_width, frame_height
        )
        right_ear = self.get_landmark_point(
            results, LANDMARK_RIGHT_EAR, frame_width, frame_height
        )
        left_shoulder = self.get_landmark_point(
            results, LANDMARK_LEFT_SHOULDER, frame_width, frame_height
        )
        right_shoulder = self.get_landmark_point(
            results, LANDMARK_RIGHT_SHOULDER, frame_width, frame_height
        )
        left_hip = self.get_landmark_point(
            results, LANDMARK_LEFT_HIP, frame_width, frame_height
        )
        right_hip = self.get_landmark_point(
            results, LANDMARK_RIGHT_HIP, frame_width, frame_height
        )

        ear = _average_points(left_ear, right_ear)
        shoulder = _average_points(left_shoulder, right_shoulder)
        hip = _average_points(left_hip, right_hip)

        if ear is None or shoulder is None or hip is None:
            return None

        return {"ear": ear, "shoulder": shoulder, "hip": hip}

    def draw_posture_line(
        self,
        frame: np.ndarray,
        points: dict,
        color: tuple = (0, 255, 0),
    ) -> None:
        """Draw the ear → shoulder → hip reference line on the frame."""
        ear = tuple(points["ear"].astype(int))
        shoulder = tuple(points["shoulder"].astype(int))
        hip = tuple(points["hip"].astype(int))
        cv2.line(frame, ear, shoulder, color, 2)
        cv2.line(frame, shoulder, hip, color, 2)
        for pt in (ear, shoulder, hip):
            cv2.circle(frame, pt, 6, color, -1)

    def release(self) -> None:
        """Release MediaPipe resources."""
        try:
            self._landmarker.close()
        except Exception:
            pass


def _average_points(
    p1: Optional[np.ndarray],
    p2: Optional[np.ndarray],
) -> Optional[np.ndarray]:
    """Average two 2-D points; use whichever is available if one is None."""
    if p1 is not None and p2 is not None:
        return (p1 + p2) / 2.0
    return p1 if p1 is not None else p2

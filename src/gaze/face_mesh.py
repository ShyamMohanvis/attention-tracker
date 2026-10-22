"""
gaze/face_mesh.py — MediaPipe FaceLandmarker wrapper (Tasks API, mediapipe ≥ 0.10).

The legacy `mp.solutions.face_mesh` was removed in mediapipe 0.10.x.
This module uses the new Tasks API (`mp.tasks.python.vision.FaceLandmarker`),
which requires a `.task` model file (downloaded automatically on first run).

Output: FaceLandmarkerResult with `.face_landmarks` — a list of 478
NormalizedLandmark objects per face (indices 0-467 = face, 468-477 = iris).
"""

from __future__ import annotations

import sys
import time
import urllib.request
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.vision import FaceLandmarkerResult

from utils.logger import get_logger

log = get_logger("face_mesh")

# ── Model file ────────────────────────────────────────────────────────────────
def _resolve_model_path() -> tuple[Path, Path]:
    """Resolve the directory and path for face_landmarker.task."""
    # 1. PyInstaller _internal or parent assets
    candidate_dirs = [
        Path(__file__).parent.parent / "assets",
    ]
    if getattr(sys, "frozen", False):
        candidate_dirs.insert(0, Path(sys.executable).parent / "assets")
        if hasattr(sys, "_MEIPASS"):
            candidate_dirs.insert(0, Path(sys._MEIPASS) / "assets")

    for d in candidate_dirs:
        model_file = d / "face_landmarker.task"
        if model_file.exists():
            return d, model_file

    default_dir = candidate_dirs[0]
    return default_dir, default_dir / "face_landmarker.task"


_ASSETS_DIR, _MODEL_PATH = _resolve_model_path()
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
)


def _ensure_model() -> None:
    """Download the face landmarker model if not already present."""
    global _ASSETS_DIR, _MODEL_PATH
    _ASSETS_DIR, _MODEL_PATH = _resolve_model_path()
    if _MODEL_PATH.exists():
        return
    _ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Downloading face_landmarker.task model (~29 MB)…")
    try:
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        log.info("Model downloaded → %s", _MODEL_PATH)
    except Exception as exc:
        log.error("Failed to download model: %s", exc)
        raise


# ── Detector wrapper ──────────────────────────────────────────────────────────

class FaceMeshDetector:
    """
    Thin wrapper around mediapipe FaceLandmarker (Tasks API, VIDEO mode).

    Usage::

        detector = FaceMeshDetector()
        result   = detector.process(bgr_frame)
        if result and result.face_landmarks:
            landmarks = result.face_landmarks[0]   # list of NormalizedLandmark
            lm = landmarks[4]                       # tip of nose
            x, y, z = lm.x, lm.y, lm.z
    """

    def __init__(
        self,
        num_faces: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        _ensure_model()

        base_opts = mp_python.BaseOptions(model_asset_path=str(_MODEL_PATH))
        opts = mp_vision.FaceLandmarkerOptions(
            base_options=base_opts,
            num_faces=num_faces,
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            running_mode=mp_vision.RunningMode.VIDEO,
        )
        self._detector = mp_vision.FaceLandmarker.create_from_options(opts)
        self._start_ms = int(time.monotonic() * 1000)
        log.info("FaceMeshDetector initialised (Tasks API, VIDEO mode)")

    # ── Public ────────────────────────────────────────────────────────────────

    def process(self, bgr_frame) -> Optional[FaceLandmarkerResult]:
        """
        Process one BGR frame and return a FaceLandmarkerResult.

        Returns None on error. Check `result.face_landmarks` before use.
        """
        try:
            rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts_ms = int(time.monotonic() * 1000) - self._start_ms
            return self._detector.detect_for_video(mp_image, ts_ms)
        except Exception as exc:
            log.warning("FaceLandmarker error: %s", exc)
            return None

    def close(self) -> None:
        try:
            self._detector.close()
        except Exception:
            pass
        log.info("FaceMeshDetector closed")

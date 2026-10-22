"""
camera/camera.py — OpenCV webcam capture with auto-detect and hot-swap.

Usage:
    cap = CameraCapture(index=0, fps=30)
    cap.open()
    frame = cap.read()   # → np.ndarray (BGR) or None
    cap.release()

Static helpers:
    CameraCapture.list_cameras() → list of (index, name) tuples
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from utils.logger import get_logger

log = get_logger("camera")

# Friendly device name via DirectShow backend (Windows)
_DS_PROP = cv2.CAP_PROP_BACKEND


def _get_camera_name(index: int) -> str:
    """Best-effort camera name via DirectShow CAP_PROP_DESCRIPTION (if available)."""
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        return f"Camera {index}"
    # OpenCV doesn't expose a reliable name API; return a human-readable fallback
    cap.release()
    return f"Camera {index}"


class CameraCapture:
    """
    Wraps cv2.VideoCapture with:
      • Named camera enumeration
      • FPS / resolution hints
      • Frame flip for mirror mode
    """

    MAX_PROBE = 8  # probe up to this many indices when listing

    def __init__(
        self,
        index: int = 0,
        fps: int = 30,
        width: int = 640,
        height: int = 480,
        mirror: bool = True,
    ) -> None:
        self.index = index
        self.fps = fps
        self.width = width
        self.height = height
        self.mirror = mirror
        self._cap: Optional[cv2.VideoCapture] = None

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def open(self) -> bool:
        """Open the camera. Returns True on success."""
        self._cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW)
        if not self._cap.isOpened():
            log.error("Could not open camera index %d", self.index)
            return False

        self._cap.set(cv2.CAP_PROP_FPS, self.fps)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        # Use MJPEG for higher throughput on USB cameras
        self._cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc("M", "J", "P", "G"))
        log.info("Camera %d opened (%dx%d @ %d FPS)", self.index, self.width, self.height, self.fps)
        return True

    def release(self) -> None:
        if self._cap and self._cap.isOpened():
            self._cap.release()
            log.info("Camera %d released", self.index)
        self._cap = None

    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    # ── Frame acquisition ────────────────────────────────────────────────────

    def read(self) -> Optional[np.ndarray]:
        """
        Read one frame.

        Returns:
            BGR np.ndarray or None if the camera is closed / frame drop.
        """
        if not self.is_open():
            return None
        ret, frame = self._cap.read()  # type: ignore[union-attr]
        if not ret or frame is None:
            log.warning("Dropped frame from camera %d", self.index)
            return None
        if self.mirror:
            frame = cv2.flip(frame, 1)
        return frame

    # ── Static helpers ───────────────────────────────────────────────────────

    @staticmethod
    def list_cameras() -> list[tuple[int, str]]:
        """
        Probe camera indices 0..MAX_PROBE and return (index, name) pairs
        for those that successfully open.
        """
        available: list[tuple[int, str]] = []
        for i in range(CameraCapture.MAX_PROBE):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                name = _get_camera_name(i)
                available.append((i, name))
                cap.release()
        log.info("Found %d camera(s): %s", len(available), available)
        return available

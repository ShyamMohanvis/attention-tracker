"""
gaze/iris.py — Extract iris centres and eye-corner landmarks from a FaceMesh result.

MediaPipe landmark indices (with refine_landmarks=True):
  Left iris  : 468, 469, 470, 471, 472  (centre = 468)
  Right iris : 473, 474, 475, 476, 477  (centre = 473)
  Left eye corners  : outer=33,  inner=133
  Right eye corners : inner=362, outer=263
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

# ── Landmark index constants ──────────────────────────────────────────────────
LEFT_IRIS_CENTER = 468
RIGHT_IRIS_CENTER = 473

LEFT_EYE_OUTER = 33
LEFT_EYE_INNER = 133
RIGHT_EYE_INNER = 362
RIGHT_EYE_OUTER = 263


@dataclass
class IrisData:
    """
    Normalised (0-1) iris positions relative to the frame and eye widths.

    Attributes:
        left_x, left_y:   Normalised iris-centre position (frame coords).
        right_x, right_y: Same for the right eye.
        left_offset:      Horizontal iris position within left eye  (0=outer, 1=inner).
        right_offset:     Horizontal iris position within right eye (0=inner, 1=outer).
    """

    left_x: float
    left_y: float
    right_x: float
    right_y: float
    left_offset: float    # 0 → looking right, 1 → looking left (for left eye)
    right_offset: float   # 0 → looking right, 1 → looking left (for right eye)

    @property
    def mean_offset(self) -> float:
        """Average horizontal iris offset across both eyes (0=looking right, 1=looking left)."""
        return (self.left_offset + self.right_offset) / 2.0


def extract_iris(landmarks) -> Optional[IrisData]:  # type: ignore[type-arg]
    """
    Extract iris data from a single face's normalised landmarks list.

    Args:
        landmarks: list of NormalizedLandmark with .x and .y in [0, 1].

    Returns:
        IrisData, or None if landmarks are unavailable.
    """
    if landmarks is None or len(landmarks) < 478:
        return None

    # ── Left iris ─────────────────────────────────────────────────────────────
    lx = landmarks[LEFT_IRIS_CENTER].x
    ly = landmarks[LEFT_IRIS_CENTER].y
    l_outer = landmarks[LEFT_EYE_OUTER].x
    l_inner = landmarks[LEFT_EYE_INNER].x
    l_width = abs(l_inner - l_outer)
    # Offset: how far iris is from outer corner (0=outer, 1=inner)
    l_offset = (lx - min(l_outer, l_inner)) / l_width if l_width > 1e-6 else 0.5
    l_offset = float(np.clip(l_offset, 0.0, 1.0))

    # ── Right iris ────────────────────────────────────────────────────────────
    rx = landmarks[RIGHT_IRIS_CENTER].x
    ry = landmarks[RIGHT_IRIS_CENTER].y
    r_inner = landmarks[RIGHT_EYE_INNER].x
    r_outer = landmarks[RIGHT_EYE_OUTER].x
    r_width = abs(r_outer - r_inner)
    r_offset = (rx - min(r_inner, r_outer)) / r_width if r_width > 1e-6 else 0.5
    r_offset = float(np.clip(r_offset, 0.0, 1.0))

    return IrisData(
        left_x=lx,
        left_y=ly,
        right_x=rx,
        right_y=ry,
        left_offset=l_offset,
        right_offset=r_offset,
    )

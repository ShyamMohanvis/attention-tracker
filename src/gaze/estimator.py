"""
gaze/estimator.py — Combines head-pose (solvePnP) and iris offset to produce gaze_x.

Output:
    gaze_x ∈ [-1, 1]
        -1 = looking hard left
         0 = looking straight ahead
        +1 = looking hard right

Algorithm:
    1. Run solvePnP on 6 canonical face points → rotation vector → Euler angles.
    2. Extract horizontal yaw (head turn left/right).
    3. Extract horizontal iris offset from IrisData.
    4. Weighted combination:  gaze_x = 0.7 * yaw_norm + 0.3 * iris_norm

The 0.7 / 0.3 weighting was chosen because head yaw dominates monitor-to-monitor
shifts (large angle), while iris offset captures small adjustments within a monitor.
"""

from __future__ import annotations

from typing import Optional

import cv2
import numpy as np

from config import FACE_MODEL_3D, SOLVEPNP_LANDMARK_INDICES
from gaze.iris import IrisData, extract_iris
from utils.logger import get_logger

log = get_logger("estimator")

# Maximum expected head yaw for normalisation (degrees)
_MAX_YAW_DEG = 45.0


class GazeEstimator:
    """
    Per-frame gaze-x estimator.

    Args:
        yaw_weight:  Weight of head-pose yaw in the combined gaze signal.
        iris_weight: Weight of iris offset.
    """

    def __init__(
        self,
        yaw_weight: float = 0.7,
        iris_weight: float = 0.3,
    ) -> None:
        self.yaw_weight = yaw_weight
        self.iris_weight = iris_weight

    # -----------------------------------------------------------------------

    def estimate(self, frame: np.ndarray, landmarks) -> Optional[float]:  # type: ignore[type-arg]
        """
        Estimate horizontal gaze direction.

        Args:
            frame:     BGR frame (used for frame dimensions).
            landmarks: Normalised landmark list from FaceMesh result.

        Returns:
            gaze_x in [-1, 1], or None if estimation fails.
        """
        if landmarks is None:
            return None

        h, w = frame.shape[:2]

        # ── Head pose via solvePnP ────────────────────────────────────────────
        yaw_norm = self._head_yaw(landmarks, w, h)

        # ── Iris offset ───────────────────────────────────────────────────────
        iris_data = extract_iris(landmarks)
        if iris_data is None:
            iris_norm = 0.0
        else:
            # mean_offset: 0 = looking right, 1 = looking left
            # Convert to [-1, 1]: left = -1, right = +1
            iris_norm = -(iris_data.mean_offset - 0.5) * 2.0

        # ── Combine ───────────────────────────────────────────────────────────
        gaze_x = self.yaw_weight * yaw_norm + self.iris_weight * iris_norm
        return float(np.clip(gaze_x, -1.0, 1.0))

    # ── Private helpers ──────────────────────────────────────────────────────

    def _head_yaw(self, landmarks, w: int, h: int) -> float:
        """
        Compute normalised yaw from solvePnP.

        Returns:
            float in [-1, 1]: negative = head turned left, positive = right.
        """
        image_pts = np.array(
            [[landmarks[i].x * w, landmarks[i].y * h] for i in SOLVEPNP_LANDMARK_INDICES],
            dtype=np.float64,
        )

        focal = float(w)
        cam_matrix = np.array(
            [[focal, 0.0, w / 2.0], [0.0, focal, h / 2.0], [0.0, 0.0, 1.0]],
            dtype=np.float64,
        )
        dist_coeffs = np.zeros((4, 1), dtype=np.float64)

        success, rvec, _ = cv2.solvePnP(
            FACE_MODEL_3D,
            image_pts,
            cam_matrix,
            dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            return 0.0

        rmat, _ = cv2.Rodrigues(rvec)
        # RQDecomp3x3 returns Euler angles in degrees
        angles, *_ = cv2.RQDecomp3x3(rmat)
        yaw_deg = angles[1]  # rotation around Y axis

        return float(np.clip(yaw_deg / _MAX_YAW_DEG, -1.0, 1.0))

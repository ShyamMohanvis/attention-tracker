"""
gaze/classifier.py — Nearest-centroid monitor classifier.

After calibration:
  • monitor1_centroid = mean(gaze_x values collected while looking at Monitor 1)
  • monitor2_centroid = mean(gaze_x values collected while looking at Monitor 2)
  • threshold = midpoint of the two centroids

Classification:
  • gaze_x closer to monitor1_centroid → "MONITOR_1"
  • gaze_x closer to monitor2_centroid → "MONITOR_2"
  • Both centroids unavailable          → "UNKNOWN"

The classifier is direction-agnostic: if the user has Monitor 2 on the LEFT,
the calibration automatically captures the correct centroids.
"""

from __future__ import annotations

import statistics
from typing import Optional

from utils.logger import get_logger

log = get_logger("classifier")


class GazeClassifier:
    """
    Nearest-centroid monitor classifier.

    Calibrate with `fit(monitor1_samples, monitor2_samples)` before calling
    `classify(gaze_x)`.
    """

    def __init__(self) -> None:
        self._m1_centroid: Optional[float] = None
        self._m2_centroid: Optional[float] = None
        self._threshold: Optional[float] = None

    # ── Calibration ──────────────────────────────────────────────────────────

    def fit(self, monitor1_samples: list[float], monitor2_samples: list[float]) -> bool:
        """
        Fit the classifier from calibration samples.

        Args:
            monitor1_samples: gaze_x values recorded while looking at Monitor 1.
            monitor2_samples: gaze_x values recorded while looking at Monitor 2.

        Returns:
            True if calibration succeeded.
        """
        if len(monitor1_samples) < 3 or len(monitor2_samples) < 3:
            log.error("Not enough calibration samples to fit classifier")
            return False

        self._m1_centroid = statistics.mean(monitor1_samples)
        self._m2_centroid = statistics.mean(monitor2_samples)
        self._threshold = (self._m1_centroid + self._m2_centroid) / 2.0

        log.info(
            "Classifier fitted — M1 centroid=%.3f, M2 centroid=%.3f, threshold=%.3f",
            self._m1_centroid,
            self._m2_centroid,
            self._threshold,
        )
        return True

    def fit_from_settings(self, m1_values: list[float], m2_values: list[float]) -> bool:
        """Convenience wrapper that loads stored calibration from settings."""
        return self.fit(m1_values, m2_values)

    # ── Classification ───────────────────────────────────────────────────────

    def classify(self, gaze_x: float) -> str:
        """
        Classify a gaze_x value.

        Returns:
            "MONITOR_1", "MONITOR_2", or "UNKNOWN" if not yet calibrated.
        """
        if self._threshold is None or self._m1_centroid is None or self._m2_centroid is None:
            return "UNKNOWN"

        # Nearest centroid
        d1 = abs(gaze_x - self._m1_centroid)
        d2 = abs(gaze_x - self._m2_centroid)
        return "MONITOR_1" if d1 <= d2 else "MONITOR_2"

    # ── State ────────────────────────────────────────────────────────────────

    @property
    def is_calibrated(self) -> bool:
        return self._threshold is not None

    @property
    def monitor1_centroid(self) -> Optional[float]:
        return self._m1_centroid

    @property
    def monitor2_centroid(self) -> Optional[float]:
        return self._m2_centroid

    def reset(self) -> None:
        self._m1_centroid = None
        self._m2_centroid = None
        self._threshold = None

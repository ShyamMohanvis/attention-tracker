"""
camera/calibration.py — Collects and stores gaze vectors for each monitor during calibration.

Workflow:
  1. CalibrationSession is created (one per run-through).
  2. UI calls `start_capture(monitor_label)`.
  3. The gaze pipeline calls `add_sample(gaze_x)` for 3 seconds.
  4. UI calls `finish_capture()` → stored internally.
  5. Repeat for the other monitor.
  6. `get_calibration_data()` returns (monitor1_values, monitor2_values).
  7. Persist via `settings.save()`.
"""

from __future__ import annotations

from typing import Optional

from utils.logger import get_logger

log = get_logger("calibration")

COLLECT_SECONDS = 3.0   # how long to gather samples per monitor
MIN_SAMPLES = 10        # minimum valid samples before accepting calibration


class CalibrationSession:
    """
    Manages a live calibration session.

    One instance is created when the user opens the CalibrationWindow and
    discarded (or persisted) when they close it.
    """

    def __init__(self) -> None:
        self._monitor1_samples: list[float] = []
        self._monitor2_samples: list[float] = []
        self._active_label: Optional[str] = None
        self._active_samples: list[float] = []
        self._monitor1_done = False
        self._monitor2_done = False

    # ── Capture control ──────────────────────────────────────────────────────

    def start_capture(self, monitor_label: str) -> None:
        """Begin collecting samples for `monitor_label` ('MONITOR_1' or 'MONITOR_2')."""
        log.info("Calibration capture started for %s", monitor_label)
        self._active_label = monitor_label
        self._active_samples = []

    def add_sample(self, gaze_x: float) -> None:
        """Feed one gaze-x value while capture is active."""
        if self._active_label is not None:
            self._active_samples.append(gaze_x)

    def finish_capture(self) -> bool:
        """
        Finalise the current capture.

        Returns:
            True if enough samples were collected, False otherwise.
        """
        if self._active_label is None:
            return False

        if len(self._active_samples) < MIN_SAMPLES:
            log.warning(
                "Calibration for %s had only %d samples (need %d)",
                self._active_label,
                len(self._active_samples),
                MIN_SAMPLES,
            )
            self._active_label = None
            return False

        if self._active_label == "MONITOR_1":
            self._monitor1_samples = list(self._active_samples)
            self._monitor1_done = True
        elif self._active_label == "MONITOR_2":
            self._monitor2_samples = list(self._active_samples)
            self._monitor2_done = True

        log.info(
            "Calibration for %s done — %d samples, mean=%.3f",
            self._active_label,
            len(self._active_samples),
            sum(self._active_samples) / len(self._active_samples),
        )
        self._active_label = None
        self._active_samples = []
        return True

    def cancel_capture(self) -> None:
        self._active_label = None
        self._active_samples = []

    # ── State queries ─────────────────────────────────────────────────────────

    @property
    def is_complete(self) -> bool:
        return self._monitor1_done and self._monitor2_done

    @property
    def monitor1_done(self) -> bool:
        return self._monitor1_done

    @property
    def monitor2_done(self) -> bool:
        return self._monitor2_done

    @property
    def is_capturing(self) -> bool:
        return self._active_label is not None

    @property
    def sample_count(self) -> int:
        return len(self._active_samples)

    # ── Data access ──────────────────────────────────────────────────────────

    def get_calibration_data(self) -> tuple[list[float], list[float]]:
        """Return (monitor1_samples, monitor2_samples)."""
        return self._monitor1_samples, self._monitor2_samples

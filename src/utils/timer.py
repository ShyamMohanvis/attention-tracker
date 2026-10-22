"""
utils/timer.py — A simple monotonic gaze-dwell timer.

Tracks how long gaze has been continuously on a particular target (monitor label).
Resets whenever the target changes.

Usage:
    timer = GazeTimer()
    timer.start("MONITOR_1")
    ...
    elapsed = timer.elapsed("MONITOR_1")  # None if target changed
"""

from __future__ import annotations

import time
from typing import Optional


class GazeTimer:
    """
    Monotonic timer that measures uninterrupted dwell time on a target.

    Args:
        label:   The current monitor label being timed.
        started: Epoch-time when timing began.
    """

    def __init__(self) -> None:
        self._label: Optional[str] = None
        self._start: float = 0.0

    # -----------------------------------------------------------------------
    def start(self, label: str) -> None:
        """Begin timing for `label`. Resets if `label` differs from current."""
        if label != self._label:
            self._label = label
            self._start = time.monotonic()

    def elapsed(self, label: str) -> float:
        """
        Return seconds since we started tracking `label`.
        Returns 0.0 if `label` doesn't match the current target.
        """
        if label != self._label:
            return 0.0
        return time.monotonic() - self._start

    def reset(self) -> None:
        """Clear the current timer completely."""
        self._label = None
        self._start = 0.0

    @property
    def current_label(self) -> Optional[str]:
        return self._label

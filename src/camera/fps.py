"""
camera/fps.py — Rolling-average FPS counter.

Usage:
    counter = FPSCounter(window=30)
    while True:
        counter.tick()
        print(counter.fps)
"""

from __future__ import annotations

import time
from collections import deque


class FPSCounter:
    """
    Computes a rolling-average frame rate.

    Args:
        window: Number of frame intervals to average over.
    """

    def __init__(self, window: int = 30) -> None:
        self._times: deque[float] = deque(maxlen=window)
        self._last: float = time.monotonic()

    def tick(self) -> None:
        """Call once per frame, just after reading it."""
        now = time.monotonic()
        self._times.append(now - self._last)
        self._last = now

    @property
    def fps(self) -> float:
        """Current rolling-average FPS.  Returns 0.0 before the first tick."""
        if not self._times:
            return 0.0
        avg_interval = sum(self._times) / len(self._times)
        return 1.0 / avg_interval if avg_interval > 0 else 0.0

    @property
    def fps_label(self) -> str:
        return f"{self.fps:.1f} FPS"

"""
gaze/smoothing.py — 20-frame sliding-window smoother for gaze_x values.

The smoother stores raw gaze_x floats.  The classifier converts each smoothed
value into a monitor label.  The smoother also tracks the per-label classification
distribution so the state machine can query confidence.

Usage:
    smoother = GazeSmoother(window=20)
    smoother.update(gaze_x)               # add one frame
    avg = smoother.smoothed_gaze()        # average gaze_x
    label, conf = smoother.dominant()     # ("MONITOR_1", 0.9)
"""

from __future__ import annotations

from collections import Counter, deque
from typing import Optional, Tuple


class GazeSmoother:
    """
    Sliding-window smoother over gaze_x values and their monitor classifications.

    Args:
        window: Number of frames in the window (default 20).
    """

    def __init__(self, window: int = 20) -> None:
        self._window = window
        self._gaze_buf: deque[float] = deque(maxlen=window)
        self._label_buf: deque[str] = deque(maxlen=window)

    # ── Feed ─────────────────────────────────────────────────────────────────

    def update(self, gaze_x: float, label: str = "UNKNOWN") -> None:
        """
        Add one frame's gaze estimate.

        Args:
            gaze_x: Horizontal gaze direction in [-1, 1].
            label:  Monitor classification for this frame (e.g. "MONITOR_1").
        """
        self._gaze_buf.append(gaze_x)
        self._label_buf.append(label)

    def reset(self) -> None:
        self._gaze_buf.clear()
        self._label_buf.clear()

    # ── Query ─────────────────────────────────────────────────────────────────

    def smoothed_gaze(self) -> Optional[float]:
        """Average gaze_x across the window.  None if buffer is empty."""
        if not self._gaze_buf:
            return None
        return float(sum(self._gaze_buf) / len(self._gaze_buf))

    def dominant(self) -> Tuple[str, float]:
        """
        Returns (dominant_label, confidence).

        confidence = fraction of window frames that agree with the dominant label.
        """
        if not self._label_buf:
            return "UNKNOWN", 0.0
        counts = Counter(self._label_buf)
        dominant_label, dominant_count = counts.most_common(1)[0]
        confidence = dominant_count / len(self._label_buf)
        return dominant_label, float(confidence)

    @property
    def is_full(self) -> bool:
        """True once the buffer has reached its maximum size."""
        return len(self._gaze_buf) == self._window

    @property
    def size(self) -> int:
        return len(self._gaze_buf)

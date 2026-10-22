"""
monitor/mapper.py — Maps a gaze label ("MONITOR_1") to a MonitorGeometry.

This module bridges the gaze pipeline (which speaks in "MONITOR_N" labels
derived from calibration) and the physical monitor geometry (which is needed
by the controller to focus the correct window).
"""

from __future__ import annotations

from typing import Dict, Optional

from monitor.geometry import MonitorGeometry
from monitor.monitor_detector import MonitorDetector
from utils.logger import get_logger

log = get_logger("mapper")


class MonitorMapper:
    """
    Maintains a mapping between gaze labels and physical MonitorGeometry objects.

    The mapping is built at startup using the MonitorDetector.  The UI's
    video_monitor setting determines which physical monitor corresponds to
    "MONITOR_1" in the gaze pipeline.
    """

    def __init__(self) -> None:
        self._monitors: list[MonitorGeometry] = MonitorDetector.get_monitors()
        # label → geometry, e.g. "MONITOR_1" → MonitorGeometry(index=2, ...)
        self._label_map: Dict[str, MonitorGeometry] = {}

    def refresh(self) -> None:
        """Re-enumerate monitors (call after hot-plug events)."""
        self._monitors = MonitorDetector.get_monitors()
        self._label_map = {}

    @property
    def monitors(self) -> list[MonitorGeometry]:
        return list(self._monitors)

    @property
    def count(self) -> int:
        return len(self._monitors)

    def get_by_label(self, label: str) -> Optional[MonitorGeometry]:
        """
        Return the MonitorGeometry for a gaze label ("MONITOR_1", "MONITOR_2", …).

        The label is mapped to the physical monitor with the matching index.
        i.e. "MONITOR_1" → monitors[0] (index=1), "MONITOR_2" → monitors[1], etc.
        """
        if label == "UNKNOWN":
            return None
        try:
            idx = int(label.split("_")[1])  # "MONITOR_2" → 2
        except (IndexError, ValueError):
            return None
        for m in self._monitors:
            if m.index == idx:
                return m
        return None

    def get_video_monitor(self, video_monitor_index: int) -> Optional[MonitorGeometry]:
        """Return the MonitorGeometry for the user's selected video monitor."""
        for m in self._monitors:
            if m.index == video_monitor_index:
                return m
        return None

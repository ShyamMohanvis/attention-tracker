"""
monitor/monitor_detector.py — Enumerate physical monitors via win32api.

Usage:
    monitors = MonitorDetector.get_monitors()
    for m in monitors:
        print(m)   # → "Monitor 1 [Primary] (1920×1080 @ 0,0)"
"""

from __future__ import annotations

from typing import List

from monitor.geometry import MonitorGeometry
from utils.logger import get_logger

log = get_logger("monitor_detector")

try:
    import win32api  # type: ignore[import-untyped]
    import win32con  # type: ignore[import-untyped]

    _HAS_WIN32 = True
except ImportError:
    _HAS_WIN32 = False
    log.warning("pywin32 not available — using fallback monitor detection")


def _detect_win32() -> list[MonitorGeometry]:
    """Enumerate monitors using win32api.EnumDisplayMonitors."""
    monitors: list[MonitorGeometry] = []
    raw = win32api.EnumDisplayMonitors()
    # Sort by left edge so index 1 = leftmost monitor
    raw_sorted = sorted(raw, key=lambda m: m[2][0])

    for idx, (hmonitor, _, rect) in enumerate(raw_sorted, start=1):
        x, y, right, bottom = rect
        width = right - x
        height = bottom - y
        info = win32api.GetMonitorInfo(hmonitor)
        is_primary = bool(info.get("Flags", 0) & win32con.MONITORINFOF_PRIMARY)
        monitors.append(
            MonitorGeometry(
                index=idx,
                x=x,
                y=y,
                width=width,
                height=height,
                is_primary=is_primary,
            )
        )
    return monitors


def _detect_fallback() -> list[MonitorGeometry]:
    """Fallback: use Qt screen info (PySide6 must already be imported by app.py)."""
    try:
        from PySide6.QtWidgets import QApplication  # noqa: PLC0415

        app = QApplication.instance()
        if app is None:
            return [MonitorGeometry(index=1, x=0, y=0, width=1920, height=1080)]

        monitors = []
        screens = app.screens()
        for idx, screen in enumerate(screens, start=1):
            geo = screen.geometry()
            monitors.append(
                MonitorGeometry(
                    index=idx,
                    x=geo.x(),
                    y=geo.y(),
                    width=geo.width(),
                    height=geo.height(),
                    is_primary=(screen == app.primaryScreen()),
                )
            )
        return monitors
    except Exception:
        return [MonitorGeometry(index=1, x=0, y=0, width=1920, height=1080)]


class MonitorDetector:
    """Static utility for enumerating connected physical monitors."""

    @staticmethod
    def get_monitors() -> List[MonitorGeometry]:
        """
        Return a list of MonitorGeometry objects sorted by left edge (index 1 = leftmost).
        """
        monitors = _detect_win32() if _HAS_WIN32 else _detect_fallback()
        for m in monitors:
            log.info("Detected %s", m)
        return monitors

    @staticmethod
    def get_monitor_by_index(index: int) -> MonitorGeometry | None:
        """Return the monitor with the given 1-based index, or None."""
        for m in MonitorDetector.get_monitors():
            if m.index == index:
                return m
        return None

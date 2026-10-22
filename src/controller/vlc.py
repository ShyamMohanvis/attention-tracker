"""
controller/vlc.py — VLC media player controller.

Strategy: Find a VLC window on the video monitor and send Space via win32api.
VLC also exposes an RC (Remote Control) interface on a local socket, but that
requires the user to configure VLC — window focus is more reliable for v1.
"""

from __future__ import annotations

from typing import Optional

from controller.base import MediaController
from utils.logger import get_logger

log = get_logger("vlc")

_VLC_CLASSES = ("Qt5QWindowIcon", "Qt6QWindowIcon", "QWidget", "vlc")
_VLC_TITLE_HINTS = ("vlc media player", "vlc")


class VLCController(MediaController):
    """Sends Space to a VLC window on the target monitor."""

    def __init__(self, video_monitor_index: int = 1) -> None:
        self.video_monitor_index = video_monitor_index

    def _find_vlc_hwnd(self) -> Optional[int]:
        try:
            import win32gui  # type: ignore[import-untyped]
            from monitor.monitor_detector import MonitorDetector

            monitor = MonitorDetector.get_monitor_by_index(self.video_monitor_index)
            if monitor is None:
                return None

            found: Optional[int] = None

            def _callback(hwnd: int, _: object) -> bool:
                nonlocal found
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                title = win32gui.GetWindowText(hwnd).lower()
                if not any(hint in title for hint in _VLC_TITLE_HINTS):
                    return True
                rect = win32gui.GetWindowRect(hwnd)
                cx, cy = (rect[0] + rect[2]) // 2, (rect[1] + rect[3]) // 2
                if monitor.contains(cx, cy):
                    found = hwnd
                    return False
                return True

            win32gui.EnumWindows(_callback, None)
            return found
        except Exception as exc:
            log.debug("VLCController._find_vlc_hwnd error: %s", exc)
            return None

    def _send_space(self) -> bool:
        hwnd = self._find_vlc_hwnd()
        if hwnd is None:
            return False
        try:
            import win32gui  # type: ignore[import-untyped]
            import win32api  # type: ignore[import-untyped]
            import win32con  # type: ignore[import-untyped]

            win32gui.SetForegroundWindow(hwnd)
            win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_SPACE, 0)
            win32api.SendMessage(hwnd, win32con.WM_KEYUP, win32con.VK_SPACE, 0)
            log.debug("VLCController: sent Space to VLC hwnd=%d", hwnd)
            return True
        except Exception as exc:
            log.debug("VLCController._send_space error: %s", exc)
            return False

    def play(self) -> bool:
        return self._send_space()

    def pause(self) -> bool:
        return self._send_space()

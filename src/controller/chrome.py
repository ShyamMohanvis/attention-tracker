"""
controller/chrome.py — Chrome/Edge browser-specific controller.

Finds a Chrome or Edge window with a YouTube (or other media) tab on the
target monitor and sends Space directly to it via win32api PostMessage.

This is an optional enhancement — the WindowsMediaSessionController is
preferred because it requires no window manipulation.
"""

from __future__ import annotations

from typing import Optional

from controller.base import MediaController
from utils.logger import get_logger

log = get_logger("chrome")

_CHROME_CLASSES = ("Chrome_WidgetWin_1", "ApplicationFrameWindow")
_MEDIA_TITLE_HINTS = ("youtube", "netflix", "spotify", "twitch", "hbo", "disney")


class ChromeController(MediaController):
    """
    Sends a Space key to a Chrome/Edge window on the video monitor.

    Checks window title for known streaming service names to avoid sending
    Space to a plain-text browser tab.
    """

    def __init__(self, video_monitor_index: int = 1) -> None:
        self.video_monitor_index = video_monitor_index

    def _find_media_chrome_hwnd(self) -> Optional[int]:
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
                cls = win32gui.GetClassName(hwnd)
                if cls not in _CHROME_CLASSES:
                    return True
                title = win32gui.GetWindowText(hwnd).lower()
                if not any(hint in title for hint in _MEDIA_TITLE_HINTS):
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
            log.debug("ChromeController._find_media_chrome_hwnd error: %s", exc)
            return None

    def _send_space(self) -> bool:
        hwnd = self._find_media_chrome_hwnd()
        if hwnd is None:
            return False
        try:
            import win32gui  # type: ignore[import-untyped]
            import win32api  # type: ignore[import-untyped]
            import win32con  # type: ignore[import-untyped]

            win32gui.SetForegroundWindow(hwnd)
            win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_SPACE, 0)
            win32api.SendMessage(hwnd, win32con.WM_KEYUP, win32con.VK_SPACE, 0)
            log.debug("ChromeController: sent Space to hwnd=%d", hwnd)
            return True
        except Exception as exc:
            log.debug("ChromeController._send_space error: %s", exc)
            return False

    def play(self) -> bool:
        return self._send_space()

    def pause(self) -> bool:
        return self._send_space()

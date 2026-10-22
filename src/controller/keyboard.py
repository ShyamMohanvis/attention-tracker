"""
controller/keyboard.py — Media-key and focused-window fallback controllers.

MediaKeyController (Priority 2):
    Sends the OS media Play/Pause key via pyautogui.  Works for most players
    that register a global media hot key (VLC, Spotify, etc.).

FocusedWindowController (Priority 3):
    Only used when the other two fail.  Finds the foreground window on the
    video monitor, verifies it is a known media app (not VS Code, Explorer, etc.),
    and sends Space.
"""

from __future__ import annotations

import time
from typing import Optional

import pyautogui  # type: ignore[import-untyped]

from controller.base import MediaController
from utils.logger import get_logger

log = get_logger("keyboard")

# pyautogui safety settings
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0

# Window class / title fragments that are safe to send Space to
_SAFE_WINDOW_CLASSES = frozenset(
    [
        "Chrome_WidgetWin_1",   # Chrome / Edge
        "MozillaWindowClass",   # Firefox
        "ApplicationFrameWindow",  # UWP apps (Spotify Store)
        "VLC",
        "MediaPlayerClassicW",
    ]
)

_UNSAFE_TITLE_FRAGMENTS = frozenset(
    ["Visual Studio Code", "Code - Insiders", "Notepad", "Explorer"]
)


class MediaKeyController(MediaController):
    """
    Sends the media Play/Pause key via pyautogui.

    This is OS-global and does not require window focus, but only works
    for applications that register a media hot key.
    """

    def play(self) -> bool:
        try:
            pyautogui.press("playpause")
            log.debug("Sent media play key")
            return True
        except Exception as exc:
            log.debug("MediaKeyController.play failed: %s", exc)
            return False

    def pause(self) -> bool:
        try:
            pyautogui.press("playpause")  # toggle; same key as play
            log.debug("Sent media pause key")
            return True
        except Exception as exc:
            log.debug("MediaKeyController.pause failed: %s", exc)
            return False


class FocusedWindowController(MediaController):
    """
    Last-resort controller: finds the browser/player window on the video
    monitor, verifies it is safe, focuses it, and presses Space.

    Will NOT send Space to VS Code, Notepad, or Explorer.
    """

    def __init__(self, video_monitor_index: int = 1) -> None:
        self.video_monitor_index = video_monitor_index

    def _find_safe_window(self) -> Optional[int]:
        """
        Return the HWND of a safe media window on the video monitor.
        Returns None if no safe window is found.
        """
        try:
            import win32gui  # type: ignore[import-untyped]
            import win32api  # type: ignore[import-untyped]
            import win32con  # type: ignore[import-untyped]
            from monitor.monitor_detector import MonitorDetector

            monitor = MonitorDetector.get_monitor_by_index(self.video_monitor_index)
            if monitor is None:
                return None

            found_hwnd: Optional[int] = None

            def _enum_callback(hwnd: int, _: object) -> bool:
                nonlocal found_hwnd
                if not win32gui.IsWindowVisible(hwnd):
                    return True
                cls = win32gui.GetClassName(hwnd)
                title = win32gui.GetWindowText(hwnd)

                # Skip unsafe windows immediately
                for fragment in _UNSAFE_TITLE_FRAGMENTS:
                    if fragment.lower() in title.lower():
                        return True

                # Must be a known safe class
                if cls not in _SAFE_WINDOW_CLASSES:
                    return True

                # Check if window is on the target monitor
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    cx = (rect[0] + rect[2]) // 2
                    cy = (rect[1] + rect[3]) // 2
                    if monitor.contains(cx, cy):
                        found_hwnd = hwnd
                        return False  # stop enumeration
                except Exception:
                    pass
                return True

            win32gui.EnumWindows(_enum_callback, None)
            return found_hwnd

        except ImportError:
            log.warning("pywin32 not available for FocusedWindowController")
            return None
        except Exception as exc:
            log.debug("FocusedWindowController._find_safe_window error: %s", exc)
            return None

    def _send_space(self) -> bool:
        hwnd = self._find_safe_window()
        if hwnd is None:
            log.debug("FocusedWindowController: no safe media window found")
            return False
        try:
            import win32gui  # type: ignore[import-untyped]
            import win32con  # type: ignore[import-untyped]

            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.05)  # give Windows time to transfer focus
            pyautogui.press("space")
            log.debug("FocusedWindowController: sent Space to hwnd=%d", hwnd)
            return True
        except Exception as exc:
            log.debug("FocusedWindowController._send_space error: %s", exc)
            return False

    def play(self) -> bool:
        return self._send_space()

    def pause(self) -> bool:
        return self._send_space()

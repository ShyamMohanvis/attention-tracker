"""
controller/spotify.py — Spotify controller.

Spotify registers with the Windows Media Session API, so the
WindowsMediaSessionController already handles it.  This module is a
thin explicit wrapper for cases where Spotify-specific behaviour is needed
in future (e.g. direct API calls via the Spotify local server).

For v1 this is effectively a no-op that delegates to the media key.
"""

from __future__ import annotations

import pyautogui  # type: ignore[import-untyped]

from controller.base import MediaController
from utils.logger import get_logger

log = get_logger("spotify")

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0


class SpotifyController(MediaController):
    """
    Spotify controller — sends media play/pause key.

    Spotify responds to the OS media keys even when not focused.
    The WindowsMediaSessionController is preferred; this is a dedicated
    fallback if Spotify is not the current SMTC session.
    """

    def play(self) -> bool:
        try:
            pyautogui.press("playpause")
            log.debug("SpotifyController: sent playpause")
            return True
        except Exception as exc:
            log.debug("SpotifyController.play failed: %s", exc)
            return False

    def pause(self) -> bool:
        return self.play()  # same key for Spotify

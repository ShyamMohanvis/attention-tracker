"""
controller/media_session.py — Windows Media Session API controller (Priority 1).

Uses the Windows.Media.Control WinRT API via the `winsdk` package.
Works regardless of which window has focus — this is the key advantage over
a generic Space-key approach.

Requires: Windows 10 Build 1903+ and `pip install winsdk`.
"""

from __future__ import annotations

import asyncio
import threading
from typing import Optional

from controller.base import MediaController
from utils.logger import get_logger

log = get_logger("media_session")

# ── Optional import — gracefully disabled on non-Windows / missing package ──
try:
    from winsdk.windows.media.control import (  # type: ignore[import-untyped]
        GlobalSystemMediaTransportControlsSessionManager as _MediaManager,
        GlobalSystemMediaTransportControlsSessionPlaybackStatus as _PlaybackStatus,
    )
    _HAS_WINSDK = True
except ImportError:
    _HAS_WINSDK = False
    log.warning("winsdk not available — WindowsMediaSessionController disabled")


class WindowsMediaSessionController(MediaController):
    """
    Controls the *current* Windows media session (browser, VLC, Spotify, etc.)
    via the GlobalSystemMediaTransportControlsSessionManager WinRT API.

    Because it targets the active session directly, it never accidentally sends
    a Space key to VS Code or any other non-media window.
    """

    def __init__(self) -> None:
        if not _HAS_WINSDK:
            raise RuntimeError("winsdk is not installed")

        # Run a dedicated asyncio event loop in a background daemon thread
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            name="MediaSessionLoop",
            daemon=True,
        )
        self._thread.start()
        log.info("WindowsMediaSessionController initialised")

    # ── Public interface ─────────────────────────────────────────────────────

    def play(self) -> bool:
        return self._run(self._async_play())

    def pause(self) -> bool:
        return self._run(self._async_pause())

    # ── Async helpers ────────────────────────────────────────────────────────

    def _run(self, coro) -> bool:  # type: ignore[type-arg]
        """Submit a coroutine to the background loop and wait for the result."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return bool(future.result(timeout=2.0))
        except Exception as exc:
            log.debug("Media session call failed: %s", exc)
            return False

    async def _get_session(self) -> Optional[object]:
        manager = await _MediaManager.request_async()
        session = manager.get_current_session()
        return session  # None if nothing is playing

    async def _async_play(self) -> bool:
        session = await self._get_session()
        if session is None:
            log.debug("No active media session for play")
            return False
        result = await session.try_play_async()
        log.debug("play() → %s", result)
        return bool(result)

    async def _async_pause(self) -> bool:
        session = await self._get_session()
        if session is None:
            log.debug("No active media session for pause")
            return False
        result = await session.try_pause_async()
        log.debug("pause() → %s", result)
        return bool(result)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=2.0)

    # ── Class-level availability check ───────────────────────────────────────

    @staticmethod
    def is_available() -> bool:
        return _HAS_WINSDK

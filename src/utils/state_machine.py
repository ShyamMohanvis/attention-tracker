"""
utils/state_machine.py — Two-state FSM: PLAYING ↔ PAUSED.

Transition rules
────────────────
  PLAYING  → PAUSED  : gaze on non-video monitor for ≥ pause_delay seconds
                        AND confidence ≥ threshold
  PAUSED   → PLAYING : gaze on video monitor for ≥ resume_delay seconds
                        AND confidence ≥ threshold

The machine returns an *action* string ("PLAY", "PAUSE", or None) each tick so
the caller can fire the controller without polling state.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from utils.timer import GazeTimer


class PlaybackState(Enum):
    PLAYING = auto()
    PAUSED = auto()


class GazeStateMachine:
    """
    Args:
        pause_delay:          Seconds to look away before pausing.
        resume_delay:         Seconds to look back before resuming.
        confidence_threshold: Fraction of smoothing-window frames that must agree.
        video_monitor_label:  e.g. "MONITOR_1" — the monitor that hosts the video.
    """

    def __init__(
        self,
        pause_delay: float = 1.0,
        resume_delay: float = 0.3,
        confidence_threshold: float = 0.85,
        video_monitor_label: str = "MONITOR_1",
    ) -> None:
        self._state = PlaybackState.PLAYING
        self.pause_delay = pause_delay
        self.resume_delay = resume_delay
        self.confidence_threshold = confidence_threshold
        self.video_monitor_label = video_monitor_label

        self._timer = GazeTimer()

    # ── Public API ───────────────────────────────────────────────────────────

    def update(
        self,
        monitor_label: str,
        confidence: float,
    ) -> Optional[str]:
        """
        Call once per gaze frame.

        Args:
            monitor_label: "MONITOR_1", "MONITOR_2", or "UNKNOWN"
            confidence:    float in [0, 1] – fraction of sliding-window frames agreeing

        Returns:
            "PLAY", "PAUSE", or None (no action this tick)
        """
        # Below confidence threshold → treat as unknown, don't act
        if confidence < self.confidence_threshold or monitor_label == "UNKNOWN":
            self._timer.reset()
            return None

        # Keep the dwell timer ticking for the current label
        self._timer.start(monitor_label)
        elapsed = self._timer.elapsed(monitor_label)

        if self._state is PlaybackState.PLAYING:
            if monitor_label != self.video_monitor_label:
                if elapsed >= self.pause_delay:
                    self._state = PlaybackState.PAUSED
                    self._timer.reset()
                    return "PAUSE"

        elif self._state is PlaybackState.PAUSED:
            if monitor_label == self.video_monitor_label:
                if elapsed >= self.resume_delay:
                    self._state = PlaybackState.PLAYING
                    self._timer.reset()
                    return "PLAY"

        return None

    def force_state(self, state: PlaybackState) -> None:
        """Override state externally (e.g. user clicks Stop)."""
        self._state = state
        self._timer.reset()

    def reset(self) -> None:
        self._state = PlaybackState.PLAYING
        self._timer.reset()

    @property
    def state(self) -> PlaybackState:
        return self._state

    @property
    def state_label(self) -> str:
        return self._state.name  # "PLAYING" or "PAUSED"

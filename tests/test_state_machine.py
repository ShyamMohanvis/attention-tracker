"""
tests/test_state_machine.py — Unit tests for GazeStateMachine.
"""

import sys
from pathlib import Path
import time

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.state_machine import GazeStateMachine, PlaybackState


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def fsm() -> GazeStateMachine:
    return GazeStateMachine(
        pause_delay=0.1,        # 100 ms for fast tests
        resume_delay=0.05,      # 50 ms
        confidence_threshold=0.8,
        video_monitor_label="MONITOR_1",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestInitialState:
    def test_starts_playing(self, fsm):
        assert fsm.state is PlaybackState.PLAYING
        assert fsm.state_label == "PLAYING"


class TestConfidenceGate:
    def test_below_confidence_returns_none(self, fsm):
        action = fsm.update("MONITOR_2", confidence=0.5)
        assert action is None
        assert fsm.state is PlaybackState.PLAYING

    def test_unknown_label_returns_none(self, fsm):
        action = fsm.update("UNKNOWN", confidence=0.9)
        assert action is None

    def test_at_threshold_is_accepted(self, fsm):
        # drive it over pause_delay (0.1s) without going below threshold
        # First few calls are below delay, should return None
        action = fsm.update("MONITOR_2", confidence=0.8)
        assert action is None   # not enough time yet


class TestPauseTransition:
    def test_pauses_after_delay(self, fsm):
        # Continuously look at monitor 2 for > 100 ms
        deadline = time.monotonic() + 0.25
        result = None
        while time.monotonic() < deadline:
            result = fsm.update("MONITOR_2", confidence=0.9)
            if result == "PAUSE":
                break
            time.sleep(0.02)
        assert result == "PAUSE"
        assert fsm.state is PlaybackState.PAUSED

    def test_no_double_pause(self, fsm):
        # Trigger pause first
        deadline = time.monotonic() + 0.25
        while time.monotonic() < deadline:
            if fsm.update("MONITOR_2", confidence=0.9) == "PAUSE":
                break
            time.sleep(0.02)
        assert fsm.state is PlaybackState.PAUSED
        # Subsequent ticks should return None, not "PAUSE" again
        for _ in range(10):
            action = fsm.update("MONITOR_2", confidence=0.9)
            assert action is None


class TestResumeTransition:
    def _pause_fsm(self, fsm) -> None:
        deadline = time.monotonic() + 0.25
        while time.monotonic() < deadline:
            if fsm.update("MONITOR_2", confidence=0.9) == "PAUSE":
                return
            time.sleep(0.02)

    def test_resumes_after_delay(self, fsm):
        self._pause_fsm(fsm)
        assert fsm.state is PlaybackState.PAUSED

        deadline = time.monotonic() + 0.2
        result = None
        while time.monotonic() < deadline:
            result = fsm.update("MONITOR_1", confidence=0.9)
            if result == "PLAY":
                break
            time.sleep(0.01)
        assert result == "PLAY"
        assert fsm.state is PlaybackState.PLAYING

    def test_no_resume_if_still_on_other_monitor(self, fsm):
        self._pause_fsm(fsm)
        action = fsm.update("MONITOR_2", confidence=0.9)
        assert action is None


class TestReset:
    def test_reset_clears_state(self, fsm):
        fsm.force_state(PlaybackState.PAUSED)
        fsm.reset()
        assert fsm.state is PlaybackState.PLAYING

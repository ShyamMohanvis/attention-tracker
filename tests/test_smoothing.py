"""
tests/test_smoothing.py — Unit tests for GazeSmoother.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gaze.smoothing import GazeSmoother


class TestGazeSmoother:
    def test_empty_buffer_returns_none(self):
        s = GazeSmoother(window=10)
        assert s.smoothed_gaze() is None

    def test_dominant_empty_returns_unknown(self):
        s = GazeSmoother(window=10)
        label, conf = s.dominant()
        assert label == "UNKNOWN"
        assert conf == 0.0

    def test_smoothed_gaze_averages(self):
        s = GazeSmoother(window=5)
        for v in [0.2, 0.4, 0.6]:
            s.update(v, "MONITOR_1")
        avg = s.smoothed_gaze()
        assert avg == pytest.approx(0.4, abs=1e-6)

    def test_dominant_label_majority(self):
        s = GazeSmoother(window=10)
        for _ in range(7):
            s.update(0.1, "MONITOR_1")
        for _ in range(3):
            s.update(0.9, "MONITOR_2")
        label, conf = s.dominant()
        assert label == "MONITOR_1"
        assert conf == pytest.approx(0.7, abs=1e-6)

    def test_window_is_circular(self):
        s = GazeSmoother(window=3)
        s.update(1.0, "MONITOR_2")
        s.update(1.0, "MONITOR_2")
        s.update(1.0, "MONITOR_2")
        # Now push 3 MONITOR_1 samples — should evict all MONITOR_2
        s.update(0.0, "MONITOR_1")
        s.update(0.0, "MONITOR_1")
        s.update(0.0, "MONITOR_1")
        label, conf = s.dominant()
        assert label == "MONITOR_1"
        assert conf == 1.0

    def test_is_full_flag(self):
        s = GazeSmoother(window=5)
        assert not s.is_full
        for i in range(5):
            s.update(float(i), "MONITOR_1")
        assert s.is_full

    def test_reset_clears_all(self):
        s = GazeSmoother(window=5)
        s.update(0.5, "MONITOR_1")
        s.reset()
        assert s.smoothed_gaze() is None
        label, conf = s.dominant()
        assert label == "UNKNOWN"

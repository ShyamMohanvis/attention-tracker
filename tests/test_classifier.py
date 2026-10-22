"""
tests/test_classifier.py — Unit tests for GazeClassifier.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gaze.classifier import GazeClassifier


@pytest.fixture
def clf_left_right() -> GazeClassifier:
    """Monitor 1 on LEFT (gaze_x ≈ -0.6), Monitor 2 on RIGHT (gaze_x ≈ +0.6)."""
    clf = GazeClassifier()
    m1 = [-0.65, -0.60, -0.58, -0.62, -0.63]
    m2 = [0.58, 0.62, 0.65, 0.60, 0.61]
    clf.fit(m1, m2)
    return clf


@pytest.fixture
def clf_right_left() -> GazeClassifier:
    """Monitor 1 on RIGHT (gaze_x ≈ +0.6), Monitor 2 on LEFT (gaze_x ≈ -0.6)."""
    clf = GazeClassifier()
    m1 = [0.58, 0.60, 0.64, 0.62, 0.63]
    m2 = [-0.62, -0.60, -0.58, -0.65, -0.63]
    clf.fit(m1, m2)
    return clf


class TestFit:
    def test_fit_succeeds_with_enough_samples(self):
        clf = GazeClassifier()
        assert clf.fit([-0.5] * 5, [0.5] * 5) is True

    def test_fit_fails_with_too_few_samples(self):
        clf = GazeClassifier()
        assert clf.fit([-0.5] * 2, [0.5] * 5) is False
        assert not clf.is_calibrated

    def test_centroids_are_correct(self, clf_left_right):
        assert clf_left_right.monitor1_centroid == pytest.approx(-0.616, abs=0.01)
        assert clf_left_right.monitor2_centroid == pytest.approx(0.612, abs=0.01)


class TestClassify:
    def test_unknown_before_calibration(self):
        clf = GazeClassifier()
        assert clf.classify(0.5) == "UNKNOWN"

    def test_classifies_monitor1_left(self, clf_left_right):
        assert clf_left_right.classify(-0.6) == "MONITOR_1"

    def test_classifies_monitor2_right(self, clf_left_right):
        assert clf_left_right.classify(0.6) == "MONITOR_2"

    def test_classifies_reversed_layout(self, clf_right_left):
        assert clf_right_left.classify(0.6) == "MONITOR_1"
        assert clf_right_left.classify(-0.6) == "MONITOR_2"

    def test_threshold_boundary(self, clf_left_right):
        # Value exactly between centroids goes to whichever is closer
        # centroids: -0.616 and +0.612 → midpoint ≈ -0.002
        assert clf_left_right.classify(-0.002) in ("MONITOR_1", "MONITOR_2")

    def test_classifies_ambiguous_favors_nearest(self, clf_left_right):
        # gaze_x = 0.0 is closer to monitor2 (+0.612) than monitor1 (-0.616)
        assert clf_left_right.classify(0.0) == "MONITOR_2"


class TestReset:
    def test_reset_removes_calibration(self, clf_left_right):
        clf_left_right.reset()
        assert not clf_left_right.is_calibrated
        assert clf_left_right.classify(0.5) == "UNKNOWN"

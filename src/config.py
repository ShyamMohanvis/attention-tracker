"""
config.py — Centralised settings management.

Settings are stored in settings.json (next to this file) and loaded at startup.
Any module can import `settings` as a singleton and call `.save()` to persist.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
_SRC_DIR = Path(__file__).parent
SETTINGS_PATH = _SRC_DIR / "settings.json"

# App-wide constants (never user-configurable)
APP_NAME = "Attention Tracker"
APP_VERSION = "1.0.0"
APP_ORG = "AttentionTracker"

# Gaze estimation constants
SOLVEPNP_LANDMARK_INDICES = [1, 152, 33, 263, 61, 291]  # nose, chin, eye corners, mouth corners
LEFT_IRIS_CENTER_IDX = 468
RIGHT_IRIS_CENTER_IDX = 473
LEFT_EYE_INNER_IDX = 133
LEFT_EYE_OUTER_IDX = 33
RIGHT_EYE_INNER_IDX = 362
RIGHT_EYE_OUTER_IDX = 263

# Canonical 3-D face model points (millimetres, right-hand coord)
import numpy as np  # noqa: E402 – imported here to keep config.py self-contained

FACE_MODEL_3D = np.array(
    [
        [0.0,    0.0,    0.0],     # Nose tip       – index 1
        [0.0,  -63.6,  -12.5],    # Chin            – index 152
        [-43.3,  32.7,  -26.0],   # Right eye outer – index 33
        [ 43.3,  32.7,  -26.0],   # Left eye outer  – index 263
        [-28.9, -28.9,  -24.1],   # Right mouth     – index 61
        [ 28.9, -28.9,  -24.1],   # Left mouth      – index 291
    ],
    dtype=np.float64,
)


# ---------------------------------------------------------------------------
# Settings dataclass
# ---------------------------------------------------------------------------

@dataclass
class Settings:
    # ── Gaze & state machine ─────────────────────────────────────────────────
    video_monitor: int = 1          # 1-indexed monitor that plays the video
    pause_delay: float = 1.0        # seconds gaze must be on other monitor before pause
    resume_delay: float = 0.3       # seconds gaze must be back before resume
    confidence: float = 0.85        # fraction of smoothing window that must agree

    # ── Camera ───────────────────────────────────────────────────────────────
    fps: int = 30
    camera_index: int = 0

    # ── Smoothing ────────────────────────────────────────────────────────────
    smoothing_window: int = 20      # number of frames in the sliding window

    # ── Calibration data ─────────────────────────────────────────────────────
    calibrated: bool = False
    calibration_monitor1: List[float] = field(default_factory=list)  # stored gaze_x values
    calibration_monitor2: List[float] = field(default_factory=list)

    # ── Controller priority ───────────────────────────────────────────────────
    controller_priority: List[str] = field(
        default_factory=lambda: ["windows_media_session", "media_key", "focused_window"]
    )

    # -----------------------------------------------------------------------
    @classmethod
    def load(cls) -> "Settings":
        """Load from settings.json; fall back to defaults if the file is missing or corrupt."""
        if SETTINGS_PATH.exists():
            try:
                with open(SETTINGS_PATH, encoding="utf-8") as fh:
                    raw = json.load(fh)
                # Only pick keys that exist on the dataclass to be forward-compatible
                valid_keys = cls.__dataclass_fields__.keys()  # type: ignore[attr-defined]
                filtered = {k: v for k, v in raw.items() if k in valid_keys}
                return cls(**filtered)
            except Exception:
                pass  # fall through to defaults
        return cls()

    def save(self) -> None:
        """Persist current state to settings.json."""
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=2)

    def reset_calibration(self) -> None:
        self.calibrated = False
        self.calibration_monitor1 = []
        self.calibration_monitor2 = []


# ---------------------------------------------------------------------------
# Module-level singleton — import this in other modules
# ---------------------------------------------------------------------------
settings: Settings = Settings.load()

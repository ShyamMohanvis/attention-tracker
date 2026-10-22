"""
ui/calibration_window.py — Step-by-step calibration wizard.

Flow:
  Step 1: Instruct user to look at Monitor N (the video monitor).
          Count down 3 seconds while collecting gaze samples.
          → Mark Monitor 1 done.

  Step 2: Instruct user to look at the other monitor.
          Same countdown.
          → Mark Monitor 2 done.

  Step 3: Show success and save calibration to settings.json.

The window communicates with the AttentionWorker via the calibration_session
object (thread-safe: only the UI calls start_capture / finish_capture).
"""

from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from camera.calibration import CalibrationSession
from config import settings
from utils.logger import get_logger

log = get_logger("calibration_window")

_CAPTURE_MS = 3000   # ms per monitor
_TICK_MS = 100


_QSS = """
QDialog {
    background-color: #0D1117;
    color: #E6EDF3;
}
QLabel#title {
    font-size: 22px;
    font-weight: bold;
    color: #A78BFA;
}
QLabel#subtitle {
    font-size: 13px;
    color: #8B949E;
}
QLabel#instruction {
    font-size: 16px;
    color: #E6EDF3;
    padding: 20px;
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
}
QLabel#status {
    font-size: 14px;
    font-weight: bold;
    color: #58A6FF;
}
QProgressBar {
    background: #21262D;
    border: 1px solid #30363D;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7C3AED, stop:1 #06B6D4);
    border-radius: 4px;
}
QPushButton {
    background: #7C3AED;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton:hover   { background: #6D28D9; }
QPushButton:pressed { background: #5B21B6; }
QPushButton:disabled {
    background: #21262D;
    color: #484F58;
}
QPushButton#skip {
    background: #21262D;
    color: #8B949E;
    font-weight: normal;
}
QPushButton#skip:hover { background: #30363D; }
"""

_STEP_INSTRUCTIONS = [
    ("Step 1 of 2", "👁  Look at your VIDEO monitor", "Monitor 1"),
    ("Step 2 of 2", "👁  Look at your OTHER monitor", "Monitor 2"),
]


class CalibrationWindow(QDialog):
    """
    Modal calibration wizard.

    Args:
        calibration_session: Shared CalibrationSession fed by the gaze worker.
    """

    def __init__(self, calibration_session: CalibrationSession, parent=None) -> None:
        super().__init__(parent)
        self._session = calibration_session
        self._step = 0          # 0 = monitor 1, 1 = monitor 2, 2 = done
        self._elapsed_ms = 0
        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_MS)
        self._timer.timeout.connect(self._tick)

        self.setWindowTitle("Calibration Wizard")
        self.setModal(True)
        self.setFixedSize(480, 380)
        self.setStyleSheet(_QSS)
        self._build_ui()
        self._update_step()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(32, 28, 32, 28)

        self._title_lbl = QLabel()
        self._title_lbl.setObjectName("title")
        self._title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._title_lbl)

        self._subtitle_lbl = QLabel()
        self._subtitle_lbl.setObjectName("subtitle")
        self._subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._subtitle_lbl)

        root.addSpacing(8)

        self._instruction_lbl = QLabel()
        self._instruction_lbl.setObjectName("instruction")
        self._instruction_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._instruction_lbl.setWordWrap(True)
        root.addWidget(self._instruction_lbl)

        self._status_lbl = QLabel("Press Start to begin capturing.")
        self._status_lbl.setObjectName("status")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._status_lbl)

        self._progress = QProgressBar()
        self._progress.setRange(0, _CAPTURE_MS)
        self._progress.setValue(0)
        root.addWidget(self._progress)

        root.addStretch()

        btn_row = QWidget()
        btn_layout = QVBoxLayout(btn_row)
        btn_layout.setSpacing(8)

        self._start_btn = QPushButton("▶  Start Capture")
        self._start_btn.clicked.connect(self._start_capture)
        btn_layout.addWidget(self._start_btn)

        skip_btn = QPushButton("Skip Calibration")
        skip_btn.setObjectName("skip")
        skip_btn.clicked.connect(self.reject)
        btn_layout.addWidget(skip_btn)

        root.addWidget(btn_row)

    # ── Step logic ────────────────────────────────────────────────────────────

    def _update_step(self) -> None:
        if self._step >= len(_STEP_INSTRUCTIONS):
            self._finish()
            return
        heading, instr, label = _STEP_INSTRUCTIONS[self._step]
        self._title_lbl.setText(heading)
        self._instruction_lbl.setText(instr)
        self._subtitle_lbl.setText(f"Capturing gaze data for {label}")
        self._status_lbl.setText("Press Start to begin.")
        self._progress.setValue(0)
        self._start_btn.setEnabled(True)
        self._start_btn.setText("▶  Start Capture")

    def _start_capture(self) -> None:
        label = "MONITOR_1" if self._step == 0 else "MONITOR_2"
        self._session.start_capture(label)
        self._elapsed_ms = 0
        self._start_btn.setEnabled(False)
        self._timer.start()
        self._status_lbl.setText("Capturing… keep your eyes on the target monitor.")

    def _tick(self) -> None:
        self._elapsed_ms += _TICK_MS
        self._progress.setValue(self._elapsed_ms)
        remaining = (_CAPTURE_MS - self._elapsed_ms) / 1000.0
        self._status_lbl.setText(
            f"Capturing… {remaining:.1f}s — samples: {self._session.sample_count}"
        )

        if self._elapsed_ms >= _CAPTURE_MS:
            self._timer.stop()
            ok = self._session.finish_capture()
            if ok:
                self._step += 1
                self._update_step()
            else:
                self._status_lbl.setText("⚠  Too few samples — try again.")
                self._start_btn.setEnabled(True)
                self._start_btn.setText("▶  Retry Capture")

    def _finish(self) -> None:
        """Persist calibration data and close the dialog."""
        m1, m2 = self._session.get_calibration_data()
        settings.calibration_monitor1 = m1
        settings.calibration_monitor2 = m2
        settings.calibrated = True
        settings.save()
        log.info("Calibration saved to settings.json")
        self.accept()

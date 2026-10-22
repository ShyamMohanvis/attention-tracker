"""
ui/main_window.py — Premium dark-themed control panel.

Layout:
  ┌────────────────────────────────────────────────────┐
  │  👁 Attention Tracker                     _ □ ×   │
  ├────────────────────────────────────────────────────┤
  │  ┌──────────────┐   ┌───────────────────────────┐  │
  │  │              │   │  STATUS                    │  │
  │  │  Camera      │   │  ● Camera: Connected       │  │
  │  │  Preview     │   │  👁 Watching Monitor 1     │  │
  │  │  (320×240)   │   │  ⚡ PLAYING                │  │
  │  │              │   │  📊 27.4 FPS               │  │
  │  │              │   │  🔵 Confidence: 91%         │  │
  │  └──────────────┘   └───────────────────────────┘  │
  ├────────────────────────────────────────────────────┤
  │  SETTINGS                                          │
  │  Video Monitor:  ○ Mon 1  ○ Mon 2  ○ Mon 3        │
  │  Camera:         ▼ Logitech C920                   │
  │  Pause Delay:    ──●────────────  1.0 s            │
  │  Resume Delay:   ─●─────────────  0.3 s            │
  │  Confidence:     ────●─────────  85 %              │
  ├────────────────────────────────────────────────────┤
  │  [ Calibrate ]    [ ▶ Start ]    [ ⏹ Stop ]       │
  └────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent, QFont, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config import APP_NAME, APP_VERSION, settings
from utils.logger import get_logger

log = get_logger("main_window")

_ICON_PATH = Path(__file__).parent / "icons" / "tray_icon.png"

# ─────────────────────────────────────────────────────────────────────────────
# Global stylesheet
# ─────────────────────────────────────────────────────────────────────────────
APP_QSS = """
* {
    font-family: 'Segoe UI', Arial, sans-serif;
}
QMainWindow, QWidget#centralWidget {
    background-color: #0D1117;
    color: #E6EDF3;
}
/* ── Cards ── */
QGroupBox {
    background-color: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px 16px 16px 16px;
    font-size: 11px;
    font-weight: bold;
    color: #8B949E;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    top: 2px;
}
/* ── Buttons ── */
QPushButton#primary {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #7C3AED, stop:1 #4F46E5);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    min-width: 110px;
}
QPushButton#primary:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #6D28D9, stop:1 #4338CA);
}
QPushButton#primary:pressed { background: #5B21B6; }
QPushButton#primary:disabled {
    background: #21262D;
    color: #484F58;
}
QPushButton#danger {
    background: #1F1318;
    color: #F85149;
    border: 1px solid #6E2020;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    min-width: 110px;
}
QPushButton#danger:hover { background: #2A1A1A; }
QPushButton#danger:disabled {
    background: #161B22;
    color: #484F58;
    border-color: #30363D;
}
QPushButton#calibrate {
    background: #0D1F2D;
    color: #58A6FF;
    border: 1px solid #1F4B7A;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    min-width: 110px;
}
QPushButton#calibrate:hover { background: #132640; }
/* ── Sliders ── */
QSlider::groove:horizontal {
    background: #21262D;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #7C3AED;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
    border: 2px solid #A78BFA;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #7C3AED, stop:1 #06B6D4);
    border-radius: 3px;
}
/* ── Combo ── */
QComboBox {
    background: #21262D;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 6px 10px;
    color: #E6EDF3;
    min-width: 180px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #161B22;
    border: 1px solid #30363D;
    color: #E6EDF3;
    selection-background-color: #7C3AED;
}
/* ── Radio buttons ── */
QRadioButton {
    color: #C9D1D9;
    spacing: 6px;
    font-size: 13px;
}
QRadioButton::indicator {
    width: 16px; height: 16px;
    border-radius: 8px;
    border: 2px solid #484F58;
    background: #0D1117;
}
QRadioButton::indicator:checked {
    background: #7C3AED;
    border-color: #A78BFA;
}
/* ── Labels ── */
QLabel#sectionLabel {
    color: #8B949E;
    font-size: 11px;
    letter-spacing: 1px;
}
QLabel#valueLabel {
    color: #A78BFA;
    font-size: 13px;
    font-weight: bold;
    min-width: 48px;
}
QLabel#statusValue {
    font-size: 14px;
    font-weight: bold;
}
/* ── Confidence bar ── */
QLabel#confBar {
    background: #21262D;
    border-radius: 5px;
    min-height: 8px;
}
/* ── Camera preview ── */
QLabel#preview {
    background: #0D1117;
    border: 1px solid #30363D;
    border-radius: 8px;
}
/* ── Scroll area ── */
QScrollArea { border: none; background: transparent; }
"""


def _dot(colour: str) -> str:
    """Return an HTML-coloured bullet."""
    return f'<span style="color:{colour};">●</span>'


def frame_to_pixmap(frame: np.ndarray, w: int = 320, h: int = 240) -> QPixmap:
    """Convert a BGR numpy frame to a scaled QPixmap."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_resized = cv2.resize(rgb, (w, h))
    img = QImage(
        rgb_resized.data, w, h, w * 3, QImage.Format.Format_RGB888
    )
    return QPixmap.fromImage(img)


# ─────────────────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    """
    Main application window.

    Signals (emitted by the AttentionWorker, consumed here):
        - gaze_updated(str, float)  → monitor label + confidence
        - state_changed(str)        → "PLAYING" or "PAUSED"
        - frame_ready(np.ndarray)   → raw BGR frame
        - fps_updated(float)        → current FPS
        - camera_status(bool)       → True = connected
    """

    # Outbound signals (consumed by app.py / worker)
    request_start = Signal()
    request_stop = Signal()
    request_calibrate = Signal()
    video_monitor_changed = Signal(int)
    camera_changed = Signal(int)
    pause_delay_changed = Signal(float)
    resume_delay_changed = Signal(float)
    confidence_changed = Signal(float)

    def __init__(self, camera_list: list[tuple[int, str]]) -> None:
        super().__init__()
        self._camera_list = camera_list
        self._tracking = False

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        if _ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(_ICON_PATH)))
        self.setMinimumSize(680, 600)
        self.setStyleSheet(APP_QSS)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(12)

        # ── Header ──────────────────────────────────────────────────────────
        root_layout.addWidget(self._build_header())

        # ── Top row: preview + status ────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        top_row.addWidget(self._build_preview_card(), 1)
        top_row.addWidget(self._build_status_card(), 1)
        root_layout.addLayout(top_row)

        # ── Settings card ────────────────────────────────────────────────────
        root_layout.addWidget(self._build_settings_card())

        # ── Action buttons ───────────────────────────────────────────────────
        root_layout.addWidget(self._build_action_bar())

        root_layout.addStretch()

    # ── Header ───────────────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(4, 0, 4, 0)

        icon_lbl = QLabel("👁")
        icon_lbl.setFont(QFont("Segoe UI Emoji", 24))
        layout.addWidget(icon_lbl)

        title = QLabel(APP_NAME)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #A78BFA;")
        layout.addWidget(title)

        layout.addStretch()

        ver = QLabel(f"v{APP_VERSION}")
        ver.setStyleSheet("color: #484F58; font-size: 12px;")
        layout.addWidget(ver)
        return w

    # ── Camera preview card ───────────────────────────────────────────────────

    def _build_preview_card(self) -> QGroupBox:
        box = QGroupBox("Camera Preview")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(8, 8, 8, 8)

        self._preview_lbl = QLabel("No Frame")
        self._preview_lbl.setObjectName("preview")
        self._preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_lbl.setFixedSize(320, 240)
        self._preview_lbl.setStyleSheet(
            "QLabel { color: #484F58; font-size: 13px; }"
        )
        layout.addWidget(self._preview_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        return box

    # ── Status card ───────────────────────────────────────────────────────────

    def _build_status_card(self) -> QGroupBox:
        box = QGroupBox("Status")
        layout = QVBoxLayout(box)
        layout.setSpacing(14)
        layout.setContentsMargins(16, 16, 16, 16)

        def _row(label: str) -> tuple[QLabel, QLabel]:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel(label)
            lbl.setObjectName("sectionLabel")
            lbl.setFixedWidth(120)
            val = QLabel("—")
            val.setObjectName("statusValue")
            rl.addWidget(lbl)
            rl.addWidget(val)
            rl.addStretch()
            layout.addWidget(row)
            return lbl, val

        _, self._cam_status_lbl = _row("Camera")
        _, self._monitor_lbl = _row("Looking at")
        _, self._state_lbl = _row("Playback")
        _, self._fps_lbl = _row("FPS")
        _, self._conf_lbl = _row("Confidence")

        # Confidence progress bar (custom)
        self._conf_bar = QFrame()
        self._conf_bar.setObjectName("confBar")
        self._conf_bar.setFixedHeight(8)
        self._conf_bar.setStyleSheet(
            "QFrame { background: #21262D; border-radius: 4px; }"
        )
        layout.addWidget(self._conf_bar)
        self._conf_fill = QFrame(self._conf_bar)
        self._conf_fill.setGeometry(0, 0, 0, 8)
        self._conf_fill.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #7C3AED,stop:1 #06B6D4); border-radius: 4px; }"
        )

        layout.addStretch()
        self._update_cam_status(False)
        return box

    # ── Settings card ─────────────────────────────────────────────────────────

    def _build_settings_card(self) -> QGroupBox:
        box = QGroupBox("Settings")
        grid = QGridLayout(box)
        grid.setVerticalSpacing(14)
        grid.setHorizontalSpacing(16)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setColumnStretch(1, 1)

        row = 0

        # ── Video monitor radio buttons ──────────────────────────────────────
        grid.addWidget(self._section_label("Video Monitor"), row, 0)
        self._monitor_group = QButtonGroup(self)
        monitor_row = QHBoxLayout()
        monitor_row.setSpacing(12)
        # Detect how many monitors exist
        try:
            from monitor.monitor_detector import MonitorDetector
            monitors = MonitorDetector.get_monitors()
        except Exception:
            monitors = []
        if not monitors:
            # fallback: show 3 options
            n_monitors = 3
            from monitor.geometry import MonitorGeometry
            monitors = [MonitorGeometry(i, 0, 0, 1920, 1080) for i in range(1, n_monitors + 1)]

        for m in monitors[:4]:
            rb = QRadioButton(f"Monitor {m.index}")
            rb.setChecked(m.index == settings.video_monitor)
            rb.toggled.connect(
                lambda checked, idx=m.index: self._on_monitor_changed(idx) if checked else None
            )
            self._monitor_group.addButton(rb, m.index)
            monitor_row.addWidget(rb)
        monitor_row.addStretch()

        wrapper = QWidget()
        wrapper.setLayout(monitor_row)
        grid.addWidget(wrapper, row, 1)
        row += 1

        # ── Camera dropdown ──────────────────────────────────────────────────
        grid.addWidget(self._section_label("Camera"), row, 0)
        self._camera_combo = QComboBox()
        for idx, name in self._camera_list:
            self._camera_combo.addItem(f"{name} (#{idx})", idx)
        # Select stored camera
        for i in range(self._camera_combo.count()):
            if self._camera_combo.itemData(i) == settings.camera_index:
                self._camera_combo.setCurrentIndex(i)
                break
        self._camera_combo.currentIndexChanged.connect(self._on_camera_changed)
        grid.addWidget(self._camera_combo, row, 1)
        row += 1

        # ── Pause delay slider ───────────────────────────────────────────────
        grid.addWidget(self._section_label("Pause Delay"), row, 0)
        self._pause_slider, self._pause_lbl = self._make_slider(
            min_v=2, max_v=50, value=int(settings.pause_delay * 10),
            fmt=lambda v: f"{v/10:.1f} s",
        )
        self._pause_slider.valueChanged.connect(
            lambda v: (
                self._pause_lbl.setText(f"{v/10:.1f} s"),
                self.pause_delay_changed.emit(v / 10),
            )
        )
        grid.addLayout(self._slider_row(self._pause_slider, self._pause_lbl), row, 1)
        row += 1

        # ── Resume delay slider ──────────────────────────────────────────────
        grid.addWidget(self._section_label("Resume Delay"), row, 0)
        self._resume_slider, self._resume_lbl = self._make_slider(
            min_v=1, max_v=20, value=int(settings.resume_delay * 10),
            fmt=lambda v: f"{v/10:.1f} s",
        )
        self._resume_slider.valueChanged.connect(
            lambda v: (
                self._resume_lbl.setText(f"{v/10:.1f} s"),
                self.resume_delay_changed.emit(v / 10),
            )
        )
        grid.addLayout(self._slider_row(self._resume_slider, self._resume_lbl), row, 1)
        row += 1

        # ── Confidence slider ────────────────────────────────────────────────
        grid.addWidget(self._section_label("Confidence"), row, 0)
        self._conf_slider, self._conf_setting_lbl = self._make_slider(
            min_v=50, max_v=99, value=int(settings.confidence * 100),
            fmt=lambda v: f"{v} %",
        )
        self._conf_slider.valueChanged.connect(
            lambda v: (
                self._conf_setting_lbl.setText(f"{v} %"),
                self.confidence_changed.emit(v / 100),
            )
        )
        grid.addLayout(self._slider_row(self._conf_slider, self._conf_setting_lbl), row, 1)

        return box

    # ── Action bar ────────────────────────────────────────────────────────────

    def _build_action_bar(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        self._calibrate_btn = QPushButton("🎯  Calibrate")
        self._calibrate_btn.setObjectName("calibrate")
        self._calibrate_btn.setToolTip("Open the calibration wizard")
        self._calibrate_btn.clicked.connect(self.request_calibrate)
        layout.addWidget(self._calibrate_btn)

        layout.addStretch()

        self._start_btn = QPushButton("▶  Start")
        self._start_btn.setObjectName("primary")
        self._start_btn.clicked.connect(self._on_start)
        layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("⏹  Stop")
        self._stop_btn.setObjectName("danger")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        layout.addWidget(self._stop_btn)

        return w

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionLabel")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return lbl

    @staticmethod
    def _make_slider(
        min_v: int, max_v: int, value: int, fmt
    ) -> tuple[QSlider, QLabel]:
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(value)
        lbl = QLabel(fmt(value))
        lbl.setObjectName("valueLabel")
        lbl.setFixedWidth(56)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return slider, lbl

    @staticmethod
    def _slider_row(slider: QSlider, lbl: QLabel) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(slider, 1)
        row.addWidget(lbl)
        return row

    # ── Slots: UI → settings ─────────────────────────────────────────────────

    def _on_monitor_changed(self, idx: int) -> None:
        settings.video_monitor = idx
        settings.save()
        self.video_monitor_changed.emit(idx)

    def _on_camera_changed(self, _: int) -> None:
        idx = self._camera_combo.currentData()
        if idx is not None:
            settings.camera_index = idx
            settings.save()
            self.camera_changed.emit(idx)

    def _on_start(self) -> None:
        self._tracking = True
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self.request_start.emit()

    def _on_stop(self) -> None:
        self._tracking = False
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self.request_stop.emit()

    # ── Public API (called by worker via signals) ─────────────────────────────

    @Slot(np.ndarray)
    def update_frame(self, frame: np.ndarray) -> None:
        pix = frame_to_pixmap(frame, 320, 240)
        self._preview_lbl.setPixmap(pix)

    @Slot(str, float)
    def update_gaze(self, monitor_label: str, confidence: float) -> None:
        colour = "#3FB950" if monitor_label != "UNKNOWN" else "#484F58"
        self._monitor_lbl.setText(
            f'<span style="color:{colour}">{monitor_label.replace("_", " ")}</span>'
        )
        self._monitor_lbl.setTextFormat(Qt.TextFormat.RichText)
        pct = int(confidence * 100)
        self._conf_lbl.setText(f"{pct} %")
        # Animate the confidence fill bar
        bar_w = int(self._conf_bar.width() * confidence)
        self._conf_fill.setFixedWidth(max(0, bar_w))

    @Slot(str)
    def update_state(self, state: str) -> None:
        colour = "#3FB950" if state == "PLAYING" else "#F85149"
        icon = "▶" if state == "PLAYING" else "⏸"
        self._state_lbl.setText(
            f'<span style="color:{colour}">{icon}  {state}</span>'
        )
        self._state_lbl.setTextFormat(Qt.TextFormat.RichText)

    @Slot(float)
    def update_fps(self, fps: float) -> None:
        self._fps_lbl.setText(f"{fps:.1f} FPS")

    @Slot(bool)
    def _update_cam_status(self, connected: bool) -> None:
        dot = "🟢" if connected else "🔴"
        status = "Connected" if connected else "Not Connected"
        self._cam_status_lbl.setText(f"{dot}  {status}")

    def start_tracking(self) -> None:
        self._on_start()

    def stop_tracking(self) -> None:
        self._on_stop()

    # ── Window close ─────────────────────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent) -> None:
        """Minimise to tray instead of quitting."""
        event.ignore()
        self.hide()

    def cleanup(self) -> None:
        """Called by tray Exit — stop tracking before app quit."""
        if self._tracking:
            self.request_stop.emit()

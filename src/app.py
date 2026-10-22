"""
app.py — Entry point and background worker thread.

Thread architecture:
  ┌────────────────────────────────────────────────────────────────────────┐
  │  Main Thread (Qt event loop)                                           │
  │  QApplication → MainWindow → SystemTray                               │
  └──────────────────────────────┬─────────────────────────────────────────┘
                                  │ signals / slots (thread-safe)
  ┌──────────────────────────────▼─────────────────────────────────────────┐
  │  AttentionWorker  (runs in QThread)                                    │
  │  Camera → FaceMesh → Iris → Estimator → Smoother → Classifier         │
  │  → StateMachine → MediaController                                      │
  └────────────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

# ── Path setup (run from repo root or from src/) ─────────────────────────────
_SRC = Path(__file__).parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ── Early dependency check ────────────────────────────────────────────────────
def _check_deps() -> list[str]:
    """Return list of missing/broken packages before Qt starts."""
    missing = []
    for pkg in ("numpy", "cv2", "mediapipe"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    return missing


import numpy as np
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication, QMessageBox

from camera.calibration import CalibrationSession
from camera.camera import CameraCapture
from camera.fps import FPSCounter
from config import settings
from controller.base import CompositeMediaController, MediaController
from controller.keyboard import FocusedWindowController, MediaKeyController
from controller.media_session import WindowsMediaSessionController
from gaze.classifier import GazeClassifier
from gaze.estimator import GazeEstimator
from gaze.face_mesh import FaceMeshDetector
from gaze.smoothing import GazeSmoother
from ui.calibration_window import CalibrationWindow
from ui.main_window import MainWindow
from ui.tray import SystemTray
from utils.logger import get_logger
from utils.state_machine import GazeStateMachine

log = get_logger("app")


# ─────────────────────────────────────────────────────────────────────────────
# Worker
# ─────────────────────────────────────────────────────────────────────────────

class AttentionWorker(QObject):
    """
    Background thread that runs the full gaze pipeline at camera FPS.

    Signals (consumed by MainWindow):
        frame_ready(np.ndarray) — latest BGR frame (for camera preview)
        gaze_updated(str, float) — monitor label + confidence
        state_changed(str)       — "PLAYING" or "PAUSED"
        fps_updated(float)       — rolling FPS
        camera_status(bool)      — True = camera open
    """

    frame_ready = Signal(object)      # np.ndarray
    gaze_updated = Signal(str, float)
    state_changed = Signal(str)
    fps_updated = Signal(float)
    camera_status = Signal(bool)

    def __init__(
        self,
        calibration_session: CalibrationSession,
    ) -> None:
        super().__init__()
        self._cal_session = calibration_session
        self._running = False

        # ── Pipeline objects ─────────────────────────────────────────────────
        self._camera = CameraCapture(
            index=settings.camera_index,
            fps=settings.fps,
        )
        self._face_mesh = FaceMeshDetector()
        self._estimator = GazeEstimator()
        self._smoother = GazeSmoother(window=settings.smoothing_window)
        self._classifier = GazeClassifier()
        self._state_machine = GazeStateMachine(
            pause_delay=settings.pause_delay,
            resume_delay=settings.resume_delay,
            confidence_threshold=settings.confidence,
            video_monitor_label=f"MONITOR_{settings.video_monitor}",
        )
        self._fps_counter = FPSCounter(window=30)
        self._controller: MediaController = self._build_controller()

        # Load existing calibration if available
        if settings.calibrated and settings.calibration_monitor1 and settings.calibration_monitor2:
            self._classifier.fit(
                settings.calibration_monitor1,
                settings.calibration_monitor2,
            )
            log.info("Loaded calibration from settings")

    # ── Controller factory ───────────────────────────────────────────────────

    @staticmethod
    def _build_controller() -> MediaController:
        chain: list[MediaController] = []
        if WindowsMediaSessionController.is_available():
            chain.append(WindowsMediaSessionController())
            log.info("WindowsMediaSessionController enabled")
        chain.append(MediaKeyController())
        chain.append(FocusedWindowController(settings.video_monitor))
        return CompositeMediaController(chain)

    # ── Main loop ────────────────────────────────────────────────────────────

    @Slot()
    def run(self) -> None:
        """Entry point — called when the QThread starts."""
        log.info("AttentionWorker starting…")
        opened = self._camera.open()
        self.camera_status.emit(opened)
        if not opened:
            log.error("Failed to open camera %d", settings.camera_index)
            return

        self._running = True
        prev_state = self._state_machine.state_label

        while self._running:
            frame = self._camera.read()
            if frame is None:
                time.sleep(0.01)
                continue

            self._fps_counter.tick()

            # ── Emit frame for preview (downsample to avoid UI lag) ────────
            self.frame_ready.emit(frame)

            # ── Face mesh ───────────────────────────────────────────────
            results = self._face_mesh.process(frame)
            if not results or not results.face_landmarks:
                self.gaze_updated.emit("AWAY", 1.0)
                # Feed 'AWAY' directly into the state machine so it pauses if user leaves
                action = self._state_machine.update("AWAY", 1.0)
                if action == "PLAY":
                    self._controller.play()
                    log.info(">  PLAY — gaze returned")
                elif action == "PAUSE":
                    self._controller.pause()
                    log.info("|| PAUSE — user is away")
                
                new_state = self._state_machine.state_label
                if new_state != prev_state:
                    self.state_changed.emit(new_state)
                    prev_state = new_state
                
                self.fps_updated.emit(self._fps_counter.fps)
                continue

            landmarks = results.face_landmarks[0]  # list of NormalizedLandmark

            # ── Gaze estimation ───────────────────────────────────────────
            gaze_x = self._estimator.estimate(frame, landmarks)
            if gaze_x is None:
                self.gaze_updated.emit("UNKNOWN", 0.0)
                continue

            # ── Calibration sample collection ─────────────────────────────
            if self._cal_session.is_capturing:
                self._cal_session.add_sample(gaze_x)

            # ── Classification ─────────────────────────────────────────────
            label = self._classifier.classify(gaze_x)
            self._smoother.update(gaze_x, label)
            dominant_label, confidence = self._smoother.dominant()

            self.gaze_updated.emit(dominant_label, confidence)

            # ── State machine ─────────────────────────────────────────────
            action = self._state_machine.update(dominant_label, confidence)
            if action == "PLAY":
                self._controller.play()
                log.info(">  PLAY — gaze returned to video monitor")
            elif action == "PAUSE":
                self._controller.pause()
                log.info("|| PAUSE — gaze moved to other monitor")

            new_state = self._state_machine.state_label
            if new_state != prev_state:
                self.state_changed.emit(new_state)
                prev_state = new_state

            # ── FPS ───────────────────────────────────────────────────────
            self.fps_updated.emit(self._fps_counter.fps)

        # ── Cleanup ───────────────────────────────────────────────────────
        self._camera.release()
        self._face_mesh.close()
        self.camera_status.emit(False)
        log.info("AttentionWorker stopped")

    @Slot()
    def stop(self) -> None:
        self._running = False

    # ── Settings update slots ────────────────────────────────────────────────

    @Slot(float)
    def set_pause_delay(self, v: float) -> None:
        self._state_machine.pause_delay = v
        settings.pause_delay = v
        settings.save()

    @Slot(float)
    def set_resume_delay(self, v: float) -> None:
        self._state_machine.resume_delay = v
        settings.resume_delay = v
        settings.save()

    @Slot(float)
    def set_confidence(self, v: float) -> None:
        self._state_machine.confidence_threshold = v
        settings.confidence = v
        settings.save()

    @Slot(int)
    def set_video_monitor(self, idx: int) -> None:
        self._state_machine.video_monitor_label = f"MONITOR_{idx}"
        settings.video_monitor = idx
        settings.save()

    def reload_calibration(self) -> None:
        """Call after CalibrationWindow closes successfully."""
        if settings.calibrated:
            self._classifier.fit(
                settings.calibration_monitor1,
                settings.calibration_monitor2,
            )
            self._smoother.reset()
            log.info("Calibration reloaded into classifier")


# ─────────────────────────────────────────────────────────────────────────────
# Application bootstrap
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AttentionTracker")
    app.setOrganizationName("AttentionTracker")
    app.setQuitOnLastWindowClosed(False)   # keep alive in tray

    # ── Dependency check ─────────────────────────────────────────────────────
    missing = _check_deps()
    if missing:
        QMessageBox.critical(
            None,
            "Missing Dependencies",
            f"The following packages could not be imported:\n\n"
            + "\n".join(f"  • {p}" for p in missing)
            + "\n\nRun:\n  venv\\Scripts\\pip.exe install "
            + " ".join(missing),
        )
        return 1

    camera_list = CameraCapture.list_cameras()
    if not camera_list:
        camera_list = [(0, "Default Camera")]

    # ── Shared calibration session ───────────────────────────────────────────
    cal_session = CalibrationSession()

    # ── Main window ──────────────────────────────────────────────────────────
    window = MainWindow(camera_list)
    window.show()

    # ── System tray ──────────────────────────────────────────────────────────
    if not QApplication.instance().platformName().startswith("offscreen"):
        tray = SystemTray(window, app)
        tray.show()
    else:
        tray = None

    # ── Worker + thread ──────────────────────────────────────────────────────
    worker = AttentionWorker(cal_session)
    thread = QThread()
    worker.moveToThread(thread)

    # Worker lifecycle
    thread.started.connect(worker.run)
    window.request_stop.connect(worker.stop)
    window.request_stop.connect(thread.quit)

    # Worker → window updates
    worker.frame_ready.connect(window.update_frame)
    worker.gaze_updated.connect(window.update_gaze)
    worker.state_changed.connect(window.update_state)
    worker.fps_updated.connect(window.update_fps)
    worker.camera_status.connect(window._update_cam_status)

    # Window → worker settings
    window.pause_delay_changed.connect(worker.set_pause_delay)
    window.resume_delay_changed.connect(worker.set_resume_delay)
    window.confidence_changed.connect(worker.set_confidence)
    window.video_monitor_changed.connect(worker.set_video_monitor)

    # Tray tracking state sync
    if tray:
        worker.camera_status.connect(
            lambda ok: tray.set_tracking(ok and worker._running)
        )

    # ── Auto-start tracking ───────────────────────────────────────────────────
    thread.start()

    # ── Calibration dialog ────────────────────────────────────────────────────
    def _open_calibration() -> None:
        dlg = CalibrationWindow(cal_session, window)
        if dlg.exec() == CalibrationWindow.DialogCode.Accepted:
            worker.reload_calibration()
            if tray:
                tray.notify("Attention Tracker", "Calibration complete! 🎉")
            log.info("Calibration wizard completed successfully")

    window.request_calibrate.connect(_open_calibration)

    # ── Warn if not calibrated ────────────────────────────────────────────────
    if not settings.calibrated:
        QMessageBox.information(
            window,
            "First Run",
            "Welcome to Attention Tracker!\n\n"
            "Please click 'Calibrate' to teach the app which monitor is your video monitor.\n\n"
            "The app will start tracking after calibration.",
        )

    log.info("Application started")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

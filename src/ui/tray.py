"""
ui/tray.py — System tray icon with context menu.

Keeps the app running in the background when the main window is closed.
Menu items: Show Window, Toggle Tracking, Exit.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from utils.logger import get_logger

log = get_logger("tray")

_ICON_PATH = Path(__file__).parent / "icons" / "tray_icon.png"


class SystemTray(QSystemTrayIcon):
    """
    System tray icon that controls app visibility and tracking state.

    Args:
        main_window: Reference to the main window for show/hide.
        app:         QApplication instance for quit.
    """

    def __init__(self, main_window, app: QApplication) -> None:
        icon = QIcon(str(_ICON_PATH)) if _ICON_PATH.exists() else QIcon()
        super().__init__(icon)
        self._window = main_window
        self._app = app
        self._tracking = False

        self._build_menu()
        self.setToolTip("Attention Tracker")
        self.activated.connect(self._on_activated)
        log.info("System tray initialised")

    # ── Menu ─────────────────────────────────────────────────────────────────

    def _build_menu(self) -> None:
        menu = QMenu()
        menu.setStyleSheet(
            """
            QMenu {
                background: #161B22;
                color: #E6EDF3;
                border: 1px solid #30363D;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #7C3AED; }
            QMenu::separator { background: #30363D; height: 1px; margin: 4px 0; }
            """
        )

        self._show_action = menu.addAction("👁  Show Window")
        self._show_action.triggered.connect(self._toggle_window)

        menu.addSeparator()

        self._track_action = menu.addAction("▶  Start Tracking")
        self._track_action.triggered.connect(self._toggle_tracking)

        menu.addSeparator()

        quit_action = menu.addAction("✕  Exit")
        quit_action.triggered.connect(self._quit)

        self.setContextMenu(menu)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _toggle_window(self) -> None:
        if self._window.isVisible():
            self._window.hide()
            self._show_action.setText("👁  Show Window")
        else:
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()
            self._show_action.setText("⬜ Hide Window")

    def _toggle_tracking(self) -> None:
        """Delegated to main_window; tray just updates label."""
        if self._tracking:
            self._window.stop_tracking()
        else:
            self._window.start_tracking()

    def set_tracking(self, active: bool) -> None:
        self._tracking = active
        self._track_action.setText("⏸  Pause Tracking" if active else "▶  Start Tracking")
        self.setToolTip("Attention Tracker — " + ("Active" if active else "Paused"))

    def _quit(self) -> None:
        log.info("Quit from tray")
        self._window.cleanup()
        self._app.quit()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()

    # ── Notification ─────────────────────────────────────────────────────────

    def notify(self, title: str, message: str) -> None:
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

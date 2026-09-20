"""System tray icon + menu, and system tray notifications.

The tray is the app's always-available home. Double-click opens the
dashboard; the menu exposes quick actions. `notify()` sends native system
tray notifications.
"""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ..config import Config
from ..mascots import create_mascot


class HealthTray(QSystemTrayIcon):
    open_requested = Signal()
    settings_requested = Signal()
    pause_toggled = Signal()
    break_requested = Signal()
    quit_requested = Signal()

    def __init__(self, config: Config, parent=None) -> None:
        super().__init__(parent)
        self._config = config

        # Render the tray icon from the mascot art (no external asset needed).
        icon_source = create_mascot(config.companion)
        self.setIcon(QIcon(icon_source.render_icon(64)))
        icon_source.deleteLater()
        self.setToolTip("HealthPals — Biscuit is looking after you 🐾")

        self._build_menu()
        self.activated.connect(self._on_activated)

    def _build_menu(self) -> None:
        menu = QMenu()

        open_action = QAction("Open dashboard", menu)
        open_action.triggered.connect(self.open_requested.emit)
        menu.addAction(open_action)

        self._pause_action = QAction("Pause nudges", menu)
        self._pause_action.triggered.connect(self.pause_toggled.emit)
        menu.addAction(self._pause_action)

        break_action = QAction("Nudge me now", menu)
        break_action.triggered.connect(self.break_requested.emit)
        menu.addAction(break_action)

        menu.addSeparator()

        settings_action = QAction("Settings…", menu)
        settings_action.triggered.connect(self.settings_requested.emit)
        menu.addAction(settings_action)

        quit_action = QAction("Quit HealthPals", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.refresh_pause_label()

    def refresh_pause_label(self) -> None:
        self._pause_action.setText(
            "Resume nudges" if self._config.paused else "Pause nudges"
        )

    def set_companion(self, mascot_id: str) -> None:
        source = create_mascot(mascot_id)
        self.setIcon(QIcon(source.render_icon(64)))
        source.deleteLater()

    def notify(self, title: str, message: str) -> None:
        """Show a native system tray notification balloon."""
        self.showMessage(title, message, self.icon(), 6000)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self.open_requested.emit()

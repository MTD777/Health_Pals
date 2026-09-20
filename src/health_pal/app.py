"""Application entry point and orchestration.

Owns the long-lived objects (config, scheduler, pomodoro, tray) and wires
their signals together. Keeps almost no logic of its own — it's the switchboard
that lets small, focused components stay decoupled.
"""
from __future__ import annotations

import random
import sys

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox

from . import __app_name__
from .config import PROFILE_HIGH, Config
from .models import DEFAULT_REMINDERS, Reminder
from .pomodoro import Phase, PomodoroTimer
from .scheduler import ReminderScheduler
from .sound import Chime
from .ui.main_window import MainWindow
from .ui.reminder_popup import ReminderPopup
from .ui.settings_dialog import SettingsDialog
from .ui.tray import HealthTray


class HealthPalsApp:
    def __init__(self, qapp: QApplication, server: QLocalServer | None = None) -> None:
        self._app = qapp
        self._server = server
        self._config = Config.load()

        if self._server:
            self._server.newConnection.connect(self._on_server_connection)

        self._scheduler = ReminderScheduler(self._config)
        self._pomodoro = PomodoroTimer(self._config)
        self._chime = Chime(custom_path=self._config.custom_sound_path)
        self._companion = self._config.companion
        self._popup_queue: list[Reminder] = []

        self._window = MainWindow(self._config, self._scheduler, self._pomodoro)
        self._popup = ReminderPopup(self._config)
        self._tray = HealthTray(self._config)

        self._wire()
        self._tray.show()
        self._scheduler.start()

        is_autostart = "--autostart" in sys.argv or "--minimized" in sys.argv

        if self._config.first_run:
            self._config.first_run = False
            self._config.save()
            self._show_window()
            self._tray.notify(
                "Hi, I'm Bull-dee! 🐶",
                "I'll gently remind you to move, stretch and rest. "
                "Find me in the tray anytime.",
            )
        elif not is_autostart:
            self._show_window()

    def _on_server_connection(self) -> None:
        if not self._server:
            return
        conn = self._server.nextPendingConnection()
        if conn:
            if conn.waitForReadyRead(300):
                data = conn.readAll().data().decode("utf-8", errors="ignore")
                if "show" in data:
                    self._show_window()
            else:
                self._show_window()
            conn.disconnectFromServer()

    # ------------------------------------------------------------------ #
    def _wire(self) -> None:
        # Scheduler -> reminders.
        self._scheduler.reminder_due.connect(self._show_reminder)

        # Popup actions.
        self._popup.done.connect(self._scheduler.mark_done)
        self._popup.snoozed.connect(self._scheduler.snooze)
        self._popup.dismissed.connect(self._show_next_queued)

        # Window controls.
        self._window.open_settings.connect(self._open_settings)
        self._window.pause_toggled.connect(self._on_pause_changed)
        self._window.profile_changed.connect(lambda _p: self._config.save())
        self._window.test_reminder.connect(self._nudge_now)
        self._window.quit_requested.connect(self._quit)

        # Tray controls.
        self._tray.open_requested.connect(self._show_window)
        self._tray.settings_requested.connect(self._open_settings)
        self._tray.pause_toggled.connect(self._toggle_pause)
        self._tray.break_requested.connect(self._nudge_now)
        self._tray.quit_requested.connect(self._quit)

        # Pomodoro milestones.
        self._pomodoro.finished_cycle.connect(self._on_pomodoro_finished)

    # ------------------------------------------------------------------ #
    # Reminder display
    # ------------------------------------------------------------------ #
    def _reminders_hushed(self) -> bool:
        return (
            self._config.pomodoro_pause_reminders
            and self._pomodoro.phase == Phase.FOCUS
            and self._pomodoro.is_running
        )

    def _pal_name(self) -> str:
        from .mascots import MASCOTS

        cls = MASCOTS.get(self._companion)
        return cls.display_name if cls else "Your pal"

    def _show_reminder(self, reminder: Reminder, force: bool = False) -> None:
        if not force and self._reminders_hushed():
            return
        if self._config.notification_profile == PROFILE_HIGH:
            # One popup at a time — queue the rest so they never overlap or
            # steal focus mid-animation (which could leave one stuck).
            if self._popup.isVisible():
                if reminder.id not in {r.id for r in self._popup_queue} and \
                        len(self._popup_queue) < 3:
                    self._popup_queue.append(reminder)
                return
            self._present_popup(reminder)
        else:
            message = reminder.messages[0].replace("{pal}", self._pal_name())
            self._tray.notify(f"{reminder.emoji}  {reminder.title}", message)
            self._play_chime()

    def _present_popup(self, reminder: Reminder) -> None:
        self._popup.show_reminder(reminder)
        self._play_chime()

    def _show_next_queued(self) -> None:
        if self._popup_queue and not self._config.paused:
            self._present_popup(self._popup_queue.pop(0))

    def _play_chime(self) -> None:
        if self._config.play_sounds:
            self._chime.play(self._config.custom_sound_path)

    def _nudge_now(self) -> None:
        enabled = self._scheduler.enabled_reminders()
        reminder = random.choice(enabled or list(DEFAULT_REMINDERS))
        self._show_reminder(reminder, force=True)

    # ------------------------------------------------------------------ #
    # Pause / profile
    # ------------------------------------------------------------------ #
    def _toggle_pause(self) -> None:
        self._config.paused = not self._config.paused
        self._on_pause_changed(self._config.paused)

    def _on_pause_changed(self, _paused: bool) -> None:
        self._config.save()
        self._tray.refresh_pause_label()
        self._window.refresh()

    # ------------------------------------------------------------------ #
    # Windows
    # ------------------------------------------------------------------ #
    def _show_window(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._config, self._window)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    def _on_settings_saved(self) -> None:
        self._scheduler.reschedule_all()
        self._tray.refresh_pause_label()
        self._window.refresh()
        self._chime.set_custom_path(self._config.custom_sound_path)
        # Apply a companion change live across all surfaces.
        if self._config.companion != self._companion:
            self._companion = self._config.companion
            self._window.set_companion(self._companion)
            self._popup.set_companion(self._companion)
            self._tray.set_companion(self._companion)

    # ------------------------------------------------------------------ #
    # Pomodoro
    # ------------------------------------------------------------------ #
    def _on_pomodoro_finished(self, phase: Phase) -> None:
        if phase == Phase.FOCUS:
            self._tray.notify("Focus complete! 🎉", "Lovely work — time to recharge.")
        else:
            self._tray.notify("Break's over 🐾", "Ready for another focused round?")
        if self._config.play_sounds:
            self._chime.play()

    # ------------------------------------------------------------------ #
    def _quit(self) -> None:
        if self._server:
            self._server.close()
            self._server.removeServer("HealthPals_SingleInstance_Server")
        self._scheduler.stop()
        self._config.save()
        self._tray.hide()
        self._app.quit()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setQuitOnLastWindowClosed(False)

    # Single-instance check via local socket
    server_name = "HealthPals_SingleInstance_Server"
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if socket.waitForConnected(500):
        socket.write(b"show")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return 0

    server = QLocalServer()
    server.removeServer(server_name)
    server.listen(server_name)

    # Branding: Windows taskbar identity + window/taskbar icon (if provided).
    from .branding import app_icon, set_windows_app_id

    set_windows_app_id()
    icon = app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    if not _tray_available():
        QMessageBox.critical(
            None,
            __app_name__,
            "No system tray is available on this desktop, so HealthPals "
            "can't run. Please enable a notification area and try again.",
        )
        return 1

    _app_holder.append(HealthPalsApp(app, server=server))  # keep a strong reference alive
    return app.exec()


def _tray_available() -> bool:
    from PySide6.QtWidgets import QSystemTrayIcon

    return QSystemTrayIcon.isSystemTrayAvailable()


# Prevents the app object from being garbage-collected.
_app_holder: list[HealthPalsApp] = []

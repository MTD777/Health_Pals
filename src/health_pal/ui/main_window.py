"""Main dashboard window.

Deliberately a plain framed window (not a custom-drawn frame) to keep things
simple and predictable. It hosts Biscuit, the "what's next" hint, quick
controls and the pomodoro timer.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import PROFILE_HIGH, PROFILE_LOW, Config
from ..mascots import create_mascot
from ..pomodoro import PomodoroTimer
from ..scheduler import ReminderScheduler
from .pomodoro_widget import PomodoroWidget
from .theme import GHOST_BUTTON, PRIMARY_BUTTON, Palette, app_font


def _card() -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    frame.setStyleSheet(
        "QFrame#card { background: #FFFFFF; border-radius: 20px; }"
    )
    return frame


class MainWindow(QWidget):
    """The cosy control panel."""

    open_settings = Signal()
    pause_toggled = Signal(bool)
    profile_changed = Signal(str)
    test_reminder = Signal()
    quit_requested = Signal()

    def __init__(
        self,
        config: Config,
        scheduler: ReminderScheduler,
        pomodoro: PomodoroTimer,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._scheduler = scheduler

        self.setWindowTitle("HealthPals")
        self.setMinimumSize(680, 440)

        from ..branding import app_icon

        window_icon = app_icon()
        if not window_icon.isNull():
            self.setWindowIcon(window_icon)

        self._build_ui(pomodoro)

        # Refresh the "next up" hint every few seconds.
        self._hint_timer = QTimer(self)
        self._hint_timer.setInterval(3000)
        self._hint_timer.timeout.connect(self._refresh_hint)
        self._hint_timer.start()
        self._refresh_hint()

    # ------------------------------------------------------------------ #
    def _build_ui(self, pomodoro: PomodoroTimer) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("HealthPals")
        title.setFont(app_font(20, bold=True))
        title.setStyleSheet(f"color: {Palette.INK.name()};")
        self._subtitle = QLabel("with Biscuit 🐾")
        self._subtitle.setFont(app_font(11))
        self._subtitle.setStyleSheet(f"color: {Palette.INK_SOFT.name()};")
        header.addWidget(title)
        header.addWidget(self._subtitle)
        header.addStretch(1)

        settings_btn = QPushButton("⚙ Settings")
        settings_btn.setStyleSheet(GHOST_BUTTON)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self.open_settings.emit)
        header.addWidget(settings_btn)
        outer.addLayout(header)

        body = QGridLayout()
        body.setSpacing(16)
        body.setColumnStretch(0, 1)
        body.setColumnStretch(1, 1)
        outer.addLayout(body, stretch=1)

        body.addWidget(self._companion_card(), 0, 0)
        body.addWidget(self._pomodoro_card(pomodoro), 0, 1)

    def _companion_card(self) -> QFrame:
        card = _card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self._mascot = create_mascot(self._config.companion, card)
        self._subtitle.setText(f"with {self._mascot.display_name} 🐾")
        self._mascot.setFixedSize(180, 180)
        self._mascot.start()
        self._mascot.clicked.connect(lambda: self._mascot.set_mood("wave", 2.5))
        self._mascot_layout = layout
        layout.addWidget(self._mascot, alignment=Qt.AlignmentFlag.AlignHCenter)

        self._companion_name = QLabel(f"{self._mascot.display_name} is on duty")
        name = self._companion_name
        name.setFont(app_font(14, bold=True))
        name.setStyleSheet(f"color: {Palette.INK.name()};")
        name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(name)

        self._hint = QLabel("")
        self._hint.setWordWrap(True)
        self._hint.setFont(app_font(10))
        self._hint.setStyleSheet(f"color: {Palette.INK_SOFT.name()};")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._hint)

        layout.addStretch(1)

        controls = QHBoxLayout()
        controls.setSpacing(8)
        self._pause_btn = QPushButton()
        self._pause_btn.setStyleSheet(PRIMARY_BUTTON)
        self._pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pause_btn.clicked.connect(self._toggle_pause)
        self._refresh_pause_btn()

        self._profile_btn = QPushButton()
        self._profile_btn.setStyleSheet(GHOST_BUTTON)
        self._profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._profile_btn.clicked.connect(self._toggle_profile)
        self._refresh_profile_btn()

        controls.addWidget(self._pause_btn)
        controls.addWidget(self._profile_btn)
        layout.addLayout(controls)

        peek = QPushButton("Say hi 👋")
        peek.setStyleSheet(GHOST_BUTTON)
        peek.setCursor(Qt.CursorShape.PointingHandCursor)
        peek.clicked.connect(self.test_reminder.emit)
        layout.addWidget(peek)

        return card

    def _pomodoro_card(self, pomodoro: PomodoroTimer) -> QFrame:
        card = _card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        heading = QLabel("Focus timer")
        heading.setFont(app_font(14, bold=True))
        heading.setStyleSheet(f"color: {Palette.INK.name()};")
        layout.addWidget(heading)

        layout.addWidget(PomodoroWidget(pomodoro, card), stretch=1)
        return card

    # ------------------------------------------------------------------ #
    def _refresh_hint(self) -> None:
        if self._config.paused:
            self._hint.setText("Nudges are paused. Enjoy your flow! 😌")
            return
        nxt = self._scheduler.next_up()
        if nxt is None:
            self._hint.setText("No reminders enabled yet — open Settings.")
            return
        reminder, seconds = nxt
        seconds = max(0, int(seconds))
        if seconds < 60:
            when = "in under a minute"
        else:
            when = f"in about {seconds // 60} min"
        self._hint.setText(f"Next: {reminder.emoji} {reminder.title} {when}")

    def _toggle_pause(self) -> None:
        self._config.paused = not self._config.paused
        self._refresh_pause_btn()
        self._refresh_hint()
        self.pause_toggled.emit(self._config.paused)

    def _refresh_pause_btn(self) -> None:
        self._pause_btn.setText("Resume nudges" if self._config.paused else "Pause nudges")

    def _toggle_profile(self) -> None:
        new = PROFILE_LOW if self._config.notification_profile == PROFILE_HIGH else PROFILE_HIGH
        self._config.notification_profile = new
        self._refresh_profile_btn()
        self.profile_changed.emit(new)

    def _refresh_profile_btn(self) -> None:
        if self._config.notification_profile == PROFILE_HIGH:
            self._profile_btn.setText("Style: cute popup")
        else:
            self._profile_btn.setText("Style: Windows notification")

    def refresh(self) -> None:
        self._refresh_pause_btn()
        self._refresh_profile_btn()
        self._refresh_hint()

    def set_companion(self, mascot_id: str) -> None:
        old = self._mascot
        new = create_mascot(mascot_id, old.parentWidget())
        new.setFixedSize(180, 180)
        new.clicked.connect(lambda: self._mascot.set_mood("wave", 2.5))
        self._mascot_layout.replaceWidget(old, new)
        old.stop()
        old.deleteLater()
        self._mascot = new
        if self.isVisible():
            new.start()
        self._companion_name.setText(f"{new.display_name} is on duty")
        self._subtitle.setText(f"with {new.display_name} 🐾")

    # ------------------------------------------------------------------ #
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), Palette.CREAM)
        painter.end()

    def showEvent(self, event) -> None:  # noqa: N802
        # Only animate while visible to keep idle CPU near zero.
        self._mascot.start()
        self.refresh()
        super().showEvent(event)

    def hideEvent(self, event) -> None:  # noqa: N802
        self._mascot.stop()
        super().hideEvent(event)

    def closeEvent(self, event) -> None:  # noqa: N802
        behavior = getattr(self._config, "close_behavior", "ask")
        if behavior == "quit":
            event.ignore()
            self.quit_requested.emit()
            return
        if behavior == "tray":
            event.ignore()
            self.hide()
            return

        # Ask, with an optional "remember my choice".
        box = QMessageBox(self)
        box.setWindowTitle("Close HealthPals?")
        box.setIcon(QMessageBox.Icon.Question)
        box.setText("Quit HealthPals, or keep your pal watching from the tray?")
        remember = QCheckBox("Remember my choice")
        box.setCheckBox(remember)
        quit_btn = box.addButton("Quit", QMessageBox.ButtonRole.AcceptRole)
        tray_btn = box.addButton("Minimize to tray", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(tray_btn)
        box.exec()

        event.ignore()
        if box.clickedButton() is quit_btn:
            if remember.isChecked():
                self._config.close_behavior = "quit"
                self._config.save()
            self.quit_requested.emit()
        else:
            if remember.isChecked():
                self._config.close_behavior = "tray"
                self._config.save()
            self.hide()

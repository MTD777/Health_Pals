"""High-profile reminder popup.

A small, rounded, frameless card that slides up from the bottom-right corner
with Biscuit and a speech bubble. Non-modal and auto-dismissing so it never
blocks your work — you can ignore it and it fades away on its own.
"""
from __future__ import annotations

import random

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import Config
from ..mascots import create_mascot
from ..models import Reminder
from .theme import GHOST_BUTTON, PRIMARY_BUTTON, Palette, app_font

_AUTO_DISMISS_MS = 12_000


class ReminderPopup(QWidget):
    """Cute animated nudge card."""

    done = Signal(str)     # reminder id
    snoozed = Signal(str)  # reminder id
    dismissed = Signal()   # popup hidden (any reason) — used to show the next

    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._reminder: Reminder | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(360)

        self._build_ui()

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self.dismiss)

        self._anim = QPropertyAnimation(self, b"pos", self)
        self._anim.setDuration(420)
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)

    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QFrame(self)
        card.setObjectName("popupCard")
        card.setStyleSheet("QFrame#popupCard { background: transparent; }")
        outer.addWidget(card)

        root = QHBoxLayout(card)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(12)

        self._mascot = create_mascot(self._config.companion, card)
        self._mascot.setFixedSize(92, 92)
        self._root_layout = root
        root.addWidget(
            self._mascot,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter,
        )

        right = QVBoxLayout()
        right.setSpacing(6)

        # Fixed text column width so wrapped titles report the right height.
        text_w = 224
        self._title = QLabel("Time to move!")
        self._title.setFont(app_font(13, bold=True))
        self._title.setWordWrap(True)
        self._title.setFixedWidth(text_w)
        self._title.setStyleSheet(f"color: {Palette.INK.name()};")

        self._body = QLabel("")
        self._body.setWordWrap(True)
        self._body.setFixedWidth(text_w)
        self._body.setFont(app_font(10))
        self._body.setStyleSheet(f"color: {Palette.INK_SOFT.name()};")

        right.addWidget(self._title)
        right.addWidget(self._body)
        right.addSpacing(2)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self._done_btn = QPushButton("Done ✓")
        self._done_btn.setStyleSheet(PRIMARY_BUTTON)
        self._done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._done_btn.clicked.connect(self._on_done)

        self._later_btn = QPushButton("Later")
        self._later_btn.setStyleSheet(GHOST_BUTTON)
        self._later_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._later_btn.clicked.connect(self._on_later)

        buttons.addWidget(self._done_btn)
        buttons.addWidget(self._later_btn)
        buttons.addStretch(1)
        right.addLayout(buttons)

        root.addLayout(right, stretch=1)

    # ------------------------------------------------------------------ #
    def show_reminder(self, reminder: Reminder) -> None:
        self._reminder = reminder
        self._title.setText(f"{reminder.emoji}  {reminder.title}")
        message = random.choice(reminder.messages).replace(
            "{pal}", self._mascot.display_name
        )
        if reminder.duration_hint:
            message += f"\n⏱ about {reminder.duration_hint}"
        self._body.setText(message)
        self._mascot.set_mood(reminder.mood, seconds=_AUTO_DISMISS_MS / 1000)
        self._mascot.start()

        # Size to content first so tall (wrapped) titles aren't clipped.
        self.adjustSize()
        start, end = self._corner_positions()
        self.move(start)
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.start()
        self._dismiss_timer.start(_AUTO_DISMISS_MS)

    def _corner_positions(self) -> tuple[QPoint, QPoint]:
        screen = QGuiApplication.primaryScreen().availableGeometry()
        margin = 18
        end = QPoint(
            screen.right() - self.width() - margin,
            screen.bottom() - self.height() - margin,
        )
        start = QPoint(end.x(), screen.bottom() + 20)
        return start, end

    def dismiss(self) -> None:
        if not self.isVisible():
            return
        self._dismiss_timer.stop()
        self._anim.stop()
        self._mascot.stop()
        self.hide()
        self.dismissed.emit()

    def set_companion(self, mascot_id: str) -> None:
        old = self._mascot
        new = create_mascot(mascot_id, old.parentWidget())
        new.setFixedSize(92, 92)
        self._root_layout.replaceWidget(old, new)
        old.stop()
        old.deleteLater()
        self._mascot = new

    def _on_done(self) -> None:
        if self._reminder is not None:
            self._mascot.set_mood("cheer", 1.5)
            self.done.emit(self._reminder.id)
        self.dismiss()

    def _on_later(self) -> None:
        if self._reminder is not None:
            self.snoozed.emit(self._reminder.id)
        self.dismiss()

    # ------------------------------------------------------------------ #
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 22, 22)
        # Soft drop shadow.
        painter.fillPath(path.translated(0, 3), QColor(0, 0, 0, 30))
        painter.fillPath(path, Palette.CARD)
        painter.end()

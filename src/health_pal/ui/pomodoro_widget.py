"""Pomodoro widget: a circular timer ring with simple controls.

Purely presentational — it reflects a `PomodoroTimer` and forwards button
presses to it.
"""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..pomodoro import Phase, PomodoroTimer
from .theme import GHOST_BUTTON, PRIMARY_BUTTON, Palette, app_font


class _Ring(QWidget):
    """The circular progress dial."""

    def __init__(self, timer: PomodoroTimer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._timer = timer
        self._remaining = 0
        self._total = 0
        self.setMinimumSize(190, 190)
        timer.tick.connect(self._on_tick)
        timer.phase_changed.connect(lambda _p: self.update())

    def _on_tick(self, remaining: int, total: int) -> None:
        self._remaining = remaining
        self._total = total
        self.update()

    def _phase_color(self) -> QColor:
        return {
            Phase.FOCUS: Palette.SKY,
            Phase.SHORT_BREAK: Palette.MINT,
            Phase.LONG_BREAK: Palette.MINT,
            Phase.IDLE: Palette.ACCENT,
        }[self._timer.phase]

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height()) - 16
        rect = QRectF(
            (self.width() - side) / 2, (self.height() - side) / 2, side, side
        )
        thickness = 14
        inner = rect.adjusted(thickness, thickness, -thickness, -thickness)

        # Track.
        track_pen = QPen(Palette.CREAM_DEEP, thickness)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(inner, 0, 360 * 16)

        # Progress.
        frac = (self._remaining / self._total) if self._total else 0.0
        color = self._phase_color()
        progress_pen = QPen(color, thickness)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        span = int(-360 * 16 * frac)
        painter.drawArc(inner, 90 * 16, span)

        # Time text.
        minutes, seconds = divmod(max(0, self._remaining), 60)
        painter.setPen(Palette.INK)
        painter.setFont(app_font(30, bold=True))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{minutes:02d}:{seconds:02d}")

        # Phase label.
        label = PomodoroTimer.label_for(self._timer.phase)
        painter.setPen(Palette.INK_SOFT)
        painter.setFont(app_font(11, bold=True))
        painter.drawText(
            rect.adjusted(0, side * 0.62, 0, 0),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
            label.upper(),
        )
        painter.end()


class PomodoroWidget(QWidget):
    """Ring + control buttons."""

    def __init__(self, timer: PomodoroTimer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._timer = timer

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._ring = _Ring(timer, self)
        layout.addWidget(self._ring, alignment=Qt.AlignmentFlag.AlignHCenter)

        controls = QHBoxLayout()
        controls.setSpacing(10)

        self._primary = QPushButton("Start focus")
        self._primary.setStyleSheet(PRIMARY_BUTTON)
        self._primary.setCursor(Qt.CursorShape.PointingHandCursor)
        self._primary.clicked.connect(self._toggle)

        self._skip = QPushButton("Skip")
        self._skip.setStyleSheet(GHOST_BUTTON)
        self._skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self._skip.clicked.connect(timer.skip)

        self._reset = QPushButton("Reset")
        self._reset.setStyleSheet(GHOST_BUTTON)
        self._reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset.clicked.connect(timer.reset)

        controls.addStretch(1)
        controls.addWidget(self._primary)
        controls.addWidget(self._skip)
        controls.addWidget(self._reset)
        controls.addStretch(1)
        layout.addLayout(controls)

        timer.phase_changed.connect(lambda _p: self._refresh_buttons())
        self._refresh_buttons()

    def _toggle(self) -> None:
        self._timer.toggle_pause()
        self._refresh_buttons()

    def _refresh_buttons(self) -> None:
        if self._timer.phase == Phase.IDLE:
            self._primary.setText("Start focus")
        elif self._timer.is_running:
            self._primary.setText("Pause")
        else:
            self._primary.setText("Resume")

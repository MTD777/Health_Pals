"""Base class for all companions.

Provides a shared, low-cost animation loop:
- A single ~30 FPS QTimer advances a continuous `phase` used for idle
  breathing, tail wags, etc.
- Randomised, occasional blinks.
- A transient "mood" that can briefly override the idle animation
  (wave, cheer, stretch...) and auto-returns to idle.

Subclasses only implement `paint_mascot(painter, rect)`.
"""
from __future__ import annotations

import math
import random

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QWidget


_FPS = 30
_FRAME_MS = int(1000 / _FPS)


class Mascot(QWidget):
    """A self-animating companion widget."""

    display_name: str = "Companion"
    mascot_id: str = "companion"

    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(120, 120)

        self._phase = 0.0            # continuous, seconds-ish
        self._mood = "idle"
        self._mood_ttl = 0.0         # seconds of mood remaining (0 = forever)
        self._blink = 0.0            # 0 = open, 1 = fully closed
        self._blink_active = False
        self._next_blink = random.uniform(2.0, 5.0)
        self._elapsed = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(_FRAME_MS)
        self._timer.timeout.connect(self._advance)

    # ------------------------------------------------------------------ #
    # Public control
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def set_mood(self, mood: str, seconds: float = 4.0) -> None:
        """Play an expressive mood, then drift back to idle."""
        self._mood = mood
        self._mood_ttl = seconds
        self.update()

    @property
    def mood(self) -> str:
        return self._mood

    @property
    def phase(self) -> float:
        return self._phase

    @property
    def blink(self) -> float:
        return self._blink

    def render_icon(self, size: int = 64) -> QPixmap:
        """Render a static frame to a pixmap (used for the tray icon)."""
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.paint_mascot(painter, QRectF(0, 0, size, size))
        painter.end()
        return pm

    # ------------------------------------------------------------------ #
    # Animation loop
    # ------------------------------------------------------------------ #
    def _advance(self) -> None:
        dt = _FRAME_MS / 1000.0
        self._elapsed += dt
        self._phase += dt

        # Mood countdown.
        if self._mood_ttl > 0:
            self._mood_ttl -= dt
            if self._mood_ttl <= 0:
                self._mood = "idle"

        # Blink scheduling + easing.
        if self._blink_active:
            # Quick down-up over ~0.16s.
            self._blink += dt / 0.08
            if self._blink >= 2.0:
                self._blink = 0.0
                self._blink_active = False
                self._next_blink = self._elapsed + random.uniform(2.5, 6.0)
        else:
            self._blink = 0.0
            if self._elapsed >= self._next_blink:
                self._blink_active = True
        self.update()

    def blink_amount(self) -> float:
        """Eye-closed fraction 0..1 (triangle wave while blinking)."""
        if not self._blink_active:
            return 0.0
        return 1.0 - abs(1.0 - self._blink)

    def breathe(self, amplitude: float = 0.02) -> float:
        """Gentle scale factor around 1.0 for idle breathing."""
        return 1.0 + amplitude * math.sin(self._phase * 2.2)

    # ------------------------------------------------------------------ #
    # Qt hooks
    # ------------------------------------------------------------------ #
    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.paint_mascot(painter, QRectF(self.rect()))
        painter.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_mood("cheer", 2.5)
            self.clicked.emit()
        super().mousePressEvent(event)

    # ------------------------------------------------------------------ #
    # To be implemented by companions
    # ------------------------------------------------------------------ #
    def paint_mascot(self, painter: QPainter, rect: QRectF) -> None:
        raise NotImplementedError

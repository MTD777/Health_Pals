"""Kuji — a gentle, roly-poly blue whale companion.

Like Bull-dee, Kuji is drawn entirely with QPainter and reuses the shared
mood vocabulary (idle, wave, cheer, stretch, walk, drink, eyes). Kuji floats
with a soft bob, blinks, waves a fin, and puffs a little spout when cheering.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from .base import Mascot

_BODY = QColor("#5AA9E6")
_BODY_DARK = QColor("#3E86C4")
_BELLY = QColor("#EAF6FF")
_OUTLINE = QColor("#2C5F8A")
_BLUSH = QColor(247, 168, 190, 150)
_SPOUT = QColor("#BFE4FB")


class WhaleMascot(Mascot):
    """Kuji the whale."""

    display_name = "Kuji"
    mascot_id = "kuji"

    # ------------------------------------------------------------------ #
    def paint_mascot(self, painter: QPainter, rect: QRectF) -> None:
        s = min(rect.width(), rect.height()) / 215.0
        painter.save()
        painter.translate(rect.center().x(), rect.center().y() + rect.height() * 0.02)
        painter.scale(s, s)

        t = self.phase
        mood = self.mood

        bob = math.sin(t * 1.6) * 4.0        # gentle floating
        tilt = math.sin(t * 1.2) * 2.0
        look_x = math.sin(t * 0.7) * 2.0
        squint = 0.0
        fin_wave = None
        spout = False

        if mood == "cheer":
            bob = -abs(math.sin(t * 5.0)) * 10.0
            tilt = math.sin(t * 5.0) * 4.0
            spout = True
            squint = 0.25
        elif mood == "wave":
            fin_wave = math.sin(t * 7.0) * 24.0
            tilt = 3.0
        elif mood == "stretch":
            bob = 5.0
            tilt = 8.0
            squint = 0.35
        elif mood == "walk":
            painter.translate(math.sin(t * 3.0) * 6.0, 0)
        elif mood == "drink":
            bob = 6.0
            tilt = 6.0
            look_x = -1.0
        elif mood == "eyes":
            look_x = 22.0 * (1 if math.sin(t * 0.9) >= 0 else -1)
            squint = 0.45

        painter.translate(0, bob)
        painter.rotate(tilt)

        self._draw_shadow(painter)
        if spout:
            self._draw_spout(painter, t)
        self._draw_tail(painter, t)
        self._draw_body(painter)
        self._draw_fin(painter, fin_wave)
        self._draw_face(painter, look_x, squint)

        painter.restore()

    # ------------------------------------------------------------------ #
    def _draw_shadow(self, painter: QPainter) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 30))
        painter.drawEllipse(QRectF(-70, 74, 140, 22))

    def _draw_body(self, painter: QPainter) -> None:
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(_BODY)
        # Plump teardrop body.
        painter.drawRoundedRect(QRectF(-86, -50, 150, 118), 62, 58)
        # Cream belly.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_BELLY)
        painter.drawEllipse(QRectF(-60, 6, 108, 56))
        # Belly grooves.
        painter.setPen(QPen(QColor(58, 122, 178, 90), 2))
        for i in range(3):
            y = 20 + i * 12
            painter.drawLine(QPointF(-44, y), QPointF(30, y))

    def _draw_tail(self, painter: QPainter, t: float) -> None:
        painter.save()
        painter.translate(58, -6)
        painter.rotate(math.sin(t * 3.0) * 10.0)
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(_BODY_DARK)
        path = QPainterPath()
        path.moveTo(0, 0)
        path.cubicTo(28, -30, 48, -30, 44, -8)
        path.cubicTo(58, -2, 58, 10, 44, 12)
        path.cubicTo(50, 30, 30, 30, 0, 6)
        path.closeSubpath()
        painter.drawPath(path)
        painter.restore()

    def _draw_fin(self, painter: QPainter, fin_wave: float | None) -> None:
        painter.save()
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(_BODY_DARK)
        painter.translate(-40, 20)
        if fin_wave is not None:
            painter.rotate(fin_wave)
        path = QPainterPath()
        path.moveTo(0, 0)
        path.cubicTo(-26, 6, -30, 26, -12, 34)
        path.cubicTo(-6, 22, -2, 14, 0, 0)
        path.closeSubpath()
        painter.drawPath(path)
        painter.restore()

    def _draw_spout(self, painter: QPainter, t: float) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_SPOUT)
        base_x = -6
        for i in range(5):
            phase = (t * 2.0 + i * 0.4) % 1.0
            y = -60 - phase * 40
            r = 6 * (1.0 - phase) + 2
            x = base_x + math.sin(i * 1.7) * 10 * phase
            painter.drawEllipse(QRectF(x - r, y - r, 2 * r, 2 * r))

    def _draw_face(self, painter: QPainter, look_x: float, squint: float) -> None:
        # Blush.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_BLUSH)
        painter.drawEllipse(QRectF(-50, -8, 20, 13))
        painter.drawEllipse(QRectF(16, -8, 20, 13))

        # Eyes.
        self._draw_eye(painter, -28, -18, look_x, squint)
        self._draw_eye(painter, 18, -18, look_x, squint)

        # Smile.
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        smile = QPainterPath()
        smile.moveTo(-16, 0)
        smile.cubicTo(-6, 12, 8, 12, 18, 0)
        painter.drawPath(smile)

    def _draw_eye(
        self, painter: QPainter, cx: float, cy: float, look_x: float, squint: float
    ) -> None:
        r = 14.0
        eye_rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        closed = min(1.0, self.blink_amount() + squint)

        painter.setPen(QPen(_OUTLINE, 2))
        painter.setBrush(QColor("#FFFDF8"))
        painter.drawEllipse(eye_rect)

        painter.save()
        clip = QPainterPath()
        clip.addEllipse(eye_rect)
        painter.setClipPath(clip)
        ix = cx + look_x * 0.4
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#20364A"))
        painter.drawEllipse(QRectF(ix - 8, cy - 8, 16, 16))
        painter.setBrush(QColor(255, 255, 255, 235))
        painter.drawEllipse(QRectF(ix - 6, cy - 9, 5, 5))
        painter.restore()

        if closed > 0.02:
            painter.save()
            painter.setClipPath(clip)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(_BODY)
            painter.drawRect(QRectF(cx - r, cy - r, 2 * r, 2 * r * closed))
            painter.setPen(QPen(_OUTLINE, 2))
            painter.drawLine(
                QPointF(cx - r, cy - r + 2 * r * closed),
                QPointF(cx + r, cy - r + 2 * r * closed),
            )
            painter.restore()

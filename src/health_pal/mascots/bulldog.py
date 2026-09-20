"""Biscuit — a cute brown & white bulldog with heterochromia.

Drawn entirely with QPainter (no binary art assets), so Biscuit scales
crisply to any size and animates cheaply. The left eye is sky-blue, the
right eye is warm brown, exactly as requested.

Moods (see Mascot.set_mood): idle, wave, cheer, stretch, walk, drink, eyes.
"""
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen

from ..ui.theme import Palette
from .base import Mascot

_OUTLINE = QColor("#5E3D26")


class BulldogMascot(Mascot):
    """Biscuit the bulldog."""

    display_name = "Biscuit"
    mascot_id = "biscuit"

    # ------------------------------------------------------------------ #
    def paint_mascot(self, painter: QPainter, rect: QRectF) -> None:
        # Work in a logical -105..105 canvas, scaled to fit the widget.
        s = min(rect.width(), rect.height()) / 215.0
        painter.save()
        painter.translate(rect.center().x(), rect.center().y() + rect.height() * 0.03)
        painter.scale(s, s)

        t = self.phase
        mood = self.mood

        # --- Per-mood motion parameters -------------------------------- #
        bob = 0.0
        sway = 0.0
        head_tilt = math.sin(t * 1.4) * 1.6        # gentle idle nod
        look_x = math.sin(t * 0.7) * 2.0           # eyes wander a little
        squint = 0.0
        paw_wave = None
        tongue = False
        sparkle = False

        if mood == "cheer":
            bob = -abs(math.sin(t * 6.0)) * 12.0
            head_tilt = math.sin(t * 6.0) * 4.0
            sparkle = True
            squint = 0.25
        elif mood == "wave":
            paw_wave = math.sin(t * 7.0) * 26.0
            head_tilt = 4.0
        elif mood == "stretch":
            bob = 6.0
            head_tilt = 10.0
            squint = 0.35
        elif mood == "walk":
            sway = math.sin(t * 4.0) * 6.0
            bob = -abs(math.sin(t * 8.0)) * 4.0
        elif mood == "drink":
            bob = 8.0
            head_tilt = 8.0
            tongue = True
            look_x = -1.0
        elif mood == "eyes":
            look_x = 24.0 * (1 if math.sin(t * 0.9) >= 0 else -1)
            squint = 0.45

        breathe = math.sin(t * 2.2) * 2.5

        painter.translate(sway, bob)

        self._draw_shadow(painter, breathe)
        self._draw_tail(painter, t)
        self._draw_body(painter, breathe)
        self._draw_front_paws(painter, paw_wave)

        # Head group: nod + breathe.
        painter.save()
        painter.translate(0, -8 + breathe)
        painter.rotate(head_tilt)
        self._draw_ears(painter)
        self._draw_head(painter)
        self._draw_face(painter, look_x, squint, tongue)
        painter.restore()

        if sparkle:
            self._draw_sparkles(painter, t)

        painter.restore()

    # ------------------------------------------------------------------ #
    # Pieces
    # ------------------------------------------------------------------ #
    def _draw_shadow(self, painter: QPainter, breathe: float) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 34))
        w = 118 + breathe * 2
        painter.drawEllipse(QRectF(-w / 2, 86, w, 22))

    def _draw_tail(self, painter: QPainter, t: float) -> None:
        painter.save()
        painter.translate(60, 44)
        painter.rotate(math.sin(t * 5.0) * 18.0)
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(Palette.FUR_BROWN)
        path = QPainterPath()
        path.moveTo(0, 0)
        path.cubicTo(20, -6, 26, 8, 16, 20)
        path.cubicTo(12, 10, 6, 8, 0, 12)
        path.closeSubpath()
        painter.drawPath(path)
        painter.restore()

    def _draw_body(self, painter: QPainter, breathe: float) -> None:
        painter.setPen(QPen(_OUTLINE, 3))
        # Brown back / haunches.
        painter.setBrush(Palette.FUR_BROWN)
        painter.drawRoundedRect(QRectF(-66, 6 - breathe * 0.4, 132, 104 + breathe * 0.4), 52, 48)
        # Cream belly.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Palette.FUR_CREAM)
        painter.drawEllipse(QRectF(-44, 30 - breathe * 0.3, 88, 78))

    def _draw_front_paws(self, painter: QPainter, paw_wave: float | None) -> None:
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(Palette.FUR_CREAM)

        # Left paw (may wave).
        painter.save()
        if paw_wave is not None:
            painter.translate(-42, 66)
            painter.rotate(paw_wave)
            self._paw(painter, 0, 0)
        else:
            self._paw(painter, -42, 84)
        painter.restore()

        # Right paw (planted).
        self._paw(painter, 20, 84)

    def _paw(self, painter: QPainter, x: float, y: float) -> None:
        painter.save()
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(Palette.FUR_CREAM)
        painter.drawRoundedRect(QRectF(x, y, 40, 30), 16, 16)
        painter.setPen(QPen(Palette.FUR_CREAM_SHADOW, 2))
        for i in range(1, 3):
            tx = x + 40 * i / 3
            painter.drawLine(QPointF(tx, y + 8), QPointF(tx, y + 26))
        painter.restore()

    def _draw_ears(self, painter: QPainter) -> None:
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(Palette.FUR_BROWN_DARK)
        for sign in (-1, 1):
            painter.save()
            painter.translate(sign * 60, -58)
            painter.rotate(sign * 14)
            path = QPainterPath()
            path.moveTo(0, -6)
            path.cubicTo(sign * 30, -6, sign * 34, 34, sign * 10, 44)
            path.cubicTo(sign * 2, 30, sign * -6, 12, 0, -6)
            path.closeSubpath()
            painter.drawPath(path)
            # Inner ear blush.
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(247, 183, 200, 150))
            painter.drawEllipse(QRectF(sign * 6 - 7, 6, 14, 20))
            painter.restore()

    def _draw_head(self, painter: QPainter) -> None:
        # Cream base.
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(Palette.FUR_CREAM)
        painter.drawRoundedRect(QRectF(-74, -96, 148, 118), 58, 54)

        # Brown patches around each eye/ear, leaving a cream blaze + muzzle.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(Palette.FUR_BROWN)
        painter.setClipRect(QRectF(-74, -96, 148, 74))
        for sign in (-1, 1):
            path = QPainterPath()
            # Symmetric patches with a small cream blaze down the middle.
            path.addEllipse(QRectF(sign * 34 - 30, -92, 60, 84))
            painter.drawPath(path)
        painter.setClipping(False)

    def _draw_face(
        self, painter: QPainter, look_x: float, squint: float, tongue: bool
    ) -> None:
        # Muzzle / jowls (cream lobes).
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(Palette.FUR_CREAM)
        painter.drawEllipse(QRectF(-40, -30, 44, 50))
        painter.drawEllipse(QRectF(-4, -30, 44, 50))

        # Blush cheeks.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(247, 168, 190, 120))
        painter.drawEllipse(QRectF(-52, -20, 22, 15))
        painter.drawEllipse(QRectF(30, -20, 22, 15))

        # Eyes (heterochromia): left blue, right brown.
        self._draw_eye(painter, -30, -52, Palette.EYE_BLUE, look_x, squint)
        self._draw_eye(painter, 30, -52, Palette.EYE_BROWN, look_x, squint)

        # Nose.
        painter.setPen(QPen(_OUTLINE, 2))
        painter.setBrush(Palette.NOSE)
        nose = QPainterPath()
        nose.moveTo(-15, -20)
        nose.cubicTo(-15, -30, 15, -30, 15, -20)
        nose.cubicTo(12, -10, -12, -10, -15, -20)
        painter.drawPath(nose)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255, 90))
        painter.drawEllipse(QRectF(-8, -27, 8, 5))

        # Mouth (soft bulldog smile) + optional tongue.
        painter.setPen(QPen(_OUTLINE, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        mouth = QPainterPath()
        mouth.moveTo(0, -9)
        mouth.lineTo(0, 0)
        mouth.moveTo(-18, 0)
        mouth.cubicTo(-10, 10, -4, 10, 0, 2)
        mouth.cubicTo(4, 10, 10, 10, 18, 0)
        painter.drawPath(mouth)

        if tongue:
            painter.setPen(QPen(_OUTLINE, 2))
            painter.setBrush(Palette.BLUSH)
            painter.drawRoundedRect(QRectF(-8, 2, 16, 20), 7, 7)

    def _draw_eye(
        self,
        painter: QPainter,
        cx: float,
        cy: float,
        iris: QColor,
        look_x: float,
        squint: float,
    ) -> None:
        r = 17.0
        eye_rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)

        closed = min(1.0, self.blink_amount() + squint)

        # Sclera.
        painter.setPen(QPen(_OUTLINE, 2))
        painter.setBrush(QColor("#FFFDF8"))
        painter.drawEllipse(eye_rect)

        # Iris + pupil, clipped to the eye.
        painter.save()
        clip = QPainterPath()
        clip.addEllipse(eye_rect)
        painter.setClipPath(clip)
        ix = cx + look_x * 0.4
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(iris)
        painter.drawEllipse(QRectF(ix - 12, cy - 12, 24, 24))
        painter.setBrush(QColor("#241A15"))
        painter.drawEllipse(QRectF(ix - 6.5, cy - 6.5, 13, 13))
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.drawEllipse(QRectF(ix - 5, cy - 8, 6, 6))
        painter.restore()

        # Eyelid: fur-coloured chord dropping from the top when blinking.
        if closed > 0.02:
            painter.save()
            painter.setClipPath(clip)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(Palette.FUR_BROWN)
            lid_h = 2 * r * closed
            painter.drawRect(QRectF(cx - r, cy - r, 2 * r, lid_h))
            painter.setPen(QPen(_OUTLINE, 2))
            painter.drawLine(
                QPointF(cx - r, cy - r + lid_h), QPointF(cx + r, cy - r + lid_h)
            )
            painter.restore()

    def _draw_sparkles(self, painter: QPainter, t: float) -> None:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#FFD98A"))
        points = [(-78, -70), (80, -60), (-70, 10), (74, 20)]
        for i, (x, y) in enumerate(points):
            scale = 0.6 + 0.4 * abs(math.sin(t * 4 + i))
            self._star(painter, x, y, 7 * scale)

    def _star(self, painter: QPainter, cx: float, cy: float, size: float) -> None:
        path = QPainterPath()
        for i in range(4):
            ang = math.pi / 2 * i
            path.moveTo(cx, cy)
            path.lineTo(cx + math.cos(ang) * size, cy + math.sin(ang) * size)
        pen = QPen(QColor("#FFC24D"), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)

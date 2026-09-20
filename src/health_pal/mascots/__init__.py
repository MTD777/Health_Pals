"""Mascots / companions.

Each mascot is a self-painting widget with a small set of expressive "moods".
New companions just subclass `Mascot` and register in `MASCOTS` below.
"""
from .base import Mascot
from .bulldog import BulldogMascot
from .whale import WhaleMascot

# Registry of available companions (id -> class), in menu order.
MASCOTS: dict[str, type[Mascot]] = {
    BulldogMascot.mascot_id: BulldogMascot,
    WhaleMascot.mascot_id: WhaleMascot,
}


def create_mascot(mascot_id: str, parent=None) -> Mascot:
    cls = MASCOTS.get(mascot_id, BulldogMascot)
    return cls(parent)


__all__ = ["Mascot", "BulldogMascot", "WhaleMascot", "create_mascot", "MASCOTS"]

"""Central palette, fonts and small styling helpers.

One place for all colours keeps the app visually consistent and makes
re-theming (or adding a dark mode later) a one-file change.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont


class Palette:
    # Warm, soft, friendly — a cosy "puppy den" feel.
    CREAM = QColor("#FBF3E7")
    CREAM_DEEP = QColor("#F3E4CF")
    CARD = QColor("#FFFFFF")
    INK = QColor("#4A3B32")          # soft brown text
    INK_SOFT = QColor("#8A7A6D")

    # Biscuit's coat.
    FUR_BROWN = QColor("#9C6B43")
    FUR_BROWN_DARK = QColor("#7E5231")
    FUR_CREAM = QColor("#F7E9D5")
    FUR_CREAM_SHADOW = QColor("#E9D4B8")

    # Heterochromia eyes.
    EYE_BLUE = QColor("#5AA9E6")
    EYE_BROWN = QColor("#8A5A2B")
    NOSE = QColor("#3B2C25")

    # Accents / states.
    ACCENT = QColor("#FF9E80")       # peachy coral
    ACCENT_DEEP = QColor("#F57C5A")
    MINT = QColor("#8FD3B6")         # break / rest
    SKY = QColor("#7EC4E8")          # focus
    BLUSH = QColor("#F7B7C8")
    SHADOW = QColor(0, 0, 0, 40)


def app_font(size: int = 11, bold: bool = False) -> QFont:
    font = QFont("Segoe UI", size)
    font.setBold(bold)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return font


# Reusable stylesheet snippets ------------------------------------------------

CARD_STYLE = """
QFrame#card {
    background: #FFFFFF;
    border-radius: 18px;
}
"""

PRIMARY_BUTTON = """
QPushButton {
    background: #FF9E80;
    color: white;
    border: none;
    border-radius: 14px;
    padding: 8px 18px;
    font-weight: 600;
}
QPushButton:hover { background: #FF8A66; }
QPushButton:pressed { background: #F57C5A; }
QPushButton:disabled { background: #E7D8CC; color: #B8A99C; }
"""

GHOST_BUTTON = """
QPushButton {
    background: transparent;
    color: #8A7A6D;
    border: 2px solid #E9D4B8;
    border-radius: 14px;
    padding: 7px 16px;
    font-weight: 600;
}
QPushButton:hover { background: #F3E4CF; color: #4A3B32; }
QPushButton:pressed { background: #E9D4B8; }
"""

# Dialog and form control stylesheet (ensures crisp, readable light-theme UI
# regardless of OS light/dark mode setting).
DIALOG_STYLE = """
QDialog {
    background-color: #FBF3E7;
    color: #4A3B32;
}
QScrollArea {
    background-color: #FBF3E7;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: #FBF3E7;
}
QLabel {
    color: #4A3B32;
    background: transparent;
}
QGroupBox {
    border: 2px solid #E9D4B8;
    border-radius: 14px;
    margin-top: 16px;
    padding: 16px 12px 12px 12px;
    background-color: #FFFFFF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 2px 10px;
    color: #4A3B32;
    background-color: #FBF3E7;
    border: 1.5px solid #E9D4B8;
    border-radius: 8px;
    font-weight: bold;
}
QComboBox, QSpinBox, QTimeEdit, QLineEdit {
    background-color: #FFFFFF;
    color: #4A3B32;
    border: 1.5px solid #E9D4B8;
    border-radius: 8px;
    padding: 5px 8px;
    selection-background-color: #FF9E80;
    selection-color: #FFFFFF;
    min-height: 22px;
}
QComboBox:hover, QSpinBox:hover, QTimeEdit:hover, QLineEdit:hover {
    border-color: #FF9E80;
}
QComboBox:focus, QSpinBox:focus, QTimeEdit:focus, QLineEdit:focus {
    border-color: #F57C5A;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: none;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #4A3B32;
    border: 1.5px solid #E9D4B8;
    selection-background-color: #F3E4CF;
    selection-color: #4A3B32;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #E9D4B8;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #FF9E80;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #FF9E80;
    border: 2px solid #FFFFFF;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #F57C5A;
}
QScrollBar:vertical {
    background: #FBF3E7;
    width: 10px;
    margin: 0px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #E9D4B8;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #9C6B43;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""

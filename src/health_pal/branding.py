"""App branding helpers: window/taskbar icon and Windows app identity.

The icon is loaded from the project's ``assets`` folder if present
(``icon.ico`` preferred, otherwise ``icon.png``). Nothing here requires
packaging to an .exe — setting the window icon plus a stable AppUserModelID is
enough for Windows to show our icon on the taskbar even when launched via
``pythonw run.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon

if getattr(sys, "frozen", False):
    _BASE = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    _BASE = Path(__file__).resolve().parents[2]
_ASSETS = _BASE / "assets"
APP_USER_MODEL_ID = "HealthPals.Biscuit.App"


def icon_path() -> Path | None:
    for name in ("icon.ico", "icon.png"):
        candidate = _ASSETS / name
        if candidate.exists():
            return candidate
    return None


def app_icon() -> QIcon:
    path = icon_path()
    return QIcon(str(path)) if path is not None else QIcon()


def set_windows_app_id() -> None:
    """Group the app under our own taskbar identity/icon on Windows."""
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID
        )
    except Exception:
        pass

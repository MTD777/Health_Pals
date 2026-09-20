"""Cross-platform "launch at login" support.

Only ever writes *user-scoped* startup entries — never system-wide — so no
admin/root elevation is required and the change is easy to reverse. On Windows
we use the per-user Run key; on macOS a LaunchAgent plist; on Linux an XDG
autostart .desktop file.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_ID = "HealthPals"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _launch_command() -> str:
    """The command used to relaunch the app, with paths safely quoted."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --autostart'

    python = Path(sys.executable)
    # Prefer the pythonw.exe variant on Windows to avoid a console window.
    if os.name == "nt":
        pyw = python.with_name("pythonw.exe")
        if pyw.exists():
            python = pyw
    entry = Path(__file__).resolve().parents[2] / "run.py"
    return f'"{python}" "{entry}" --autostart'


# --------------------------------------------------------------------------- #
# Windows
# --------------------------------------------------------------------------- #
def _windows_set(enabled: bool) -> bool:
    import winreg

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
    except OSError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, _RUN_KEY)
    try:
        if enabled:
            winreg.SetValueEx(
                key, APP_ID, 0, winreg.REG_SZ, _launch_command()
            )
        else:
            try:
                winreg.DeleteValue(key, APP_ID)
            except FileNotFoundError:
                pass
        return True
    finally:
        winreg.CloseKey(key)


def _windows_is_enabled() -> bool:
    import winreg

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ
        )
    except OSError:
        return False
    try:
        winreg.QueryValueEx(key, APP_ID)
        return True
    except FileNotFoundError:
        return False
    finally:
        winreg.CloseKey(key)


# --------------------------------------------------------------------------- #
# macOS
# --------------------------------------------------------------------------- #
def _macos_plist() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"com.{APP_ID.lower()}.plist"


def _macos_set(enabled: bool) -> bool:
    plist = _macos_plist()
    if enabled:
        plist.parent.mkdir(parents=True, exist_ok=True)
        python = sys.executable
        entry = Path(__file__).resolve().parents[2] / "run.py"
        plist.write_text(
            f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.{APP_ID.lower()}</string>
    <key>ProgramArguments</key>
    <array><string>{python}</string><string>{entry}</string></array>
    <key>RunAtLoad</key><true/>
</dict>
</plist>
""",
            encoding="utf-8",
        )
    elif plist.exists():
        plist.unlink()
    return True


def _macos_is_enabled() -> bool:
    return _macos_plist().exists()


# --------------------------------------------------------------------------- #
# Linux (XDG autostart)
# --------------------------------------------------------------------------- #
def _linux_desktop() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "autostart" / f"{APP_ID.lower()}.desktop"


def _linux_set(enabled: bool) -> bool:
    entry_file = _linux_desktop()
    if enabled:
        entry_file.parent.mkdir(parents=True, exist_ok=True)
        entry_file.write_text(
            f"""[Desktop Entry]
Type=Application
Name={APP_ID}
Exec={_launch_command()}
X-GNOME-Autostart-enabled=true
""",
            encoding="utf-8",
        )
    elif entry_file.exists():
        entry_file.unlink()
    return True


def _linux_is_enabled() -> bool:
    return _linux_desktop().exists()


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def set_autostart(enabled: bool) -> bool:
    """Enable/disable launch-at-login. Returns True on success."""
    try:
        if sys.platform.startswith("win"):
            return _windows_set(enabled)
        if sys.platform == "darwin":
            return _macos_set(enabled)
        return _linux_set(enabled)
    except OSError:
        return False


def is_autostart_enabled() -> bool:
    try:
        if sys.platform.startswith("win"):
            return _windows_is_enabled()
        if sys.platform == "darwin":
            return _macos_is_enabled()
        return _linux_is_enabled()
    except OSError:
        return False

# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

assets_dir = Path("assets")
datas = [("assets", "assets")] if assets_dir.exists() else []

a = Analysis(
    ["run.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "health_pal",
        "health_pal.app",
        "health_pal.autostart",
        "health_pal.branding",
        "health_pal.config",
        "health_pal.models",
        "health_pal.pomodoro",
        "health_pal.scheduler",
        "health_pal.sound",
        "health_pal.mascots",
        "health_pal.mascots.base",
        "health_pal.mascots.bulldog",
        "health_pal.mascots.whale",
        "health_pal.ui",
        "health_pal.ui.main_window",
        "health_pal.ui.pomodoro_widget",
        "health_pal.ui.reminder_popup",
        "health_pal.ui.settings_dialog",
        "health_pal.ui.theme",
        "health_pal.ui.tray",
        "PySide6.QtMultimedia",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="HealthPals",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico" if Path("assets/icon.ico").exists() else ("assets/icon.png" if Path("assets/icon.png").exists() else None),
)

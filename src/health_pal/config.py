"""Persistent user configuration for HealthPals.

Settings are stored as JSON in the user's home directory so they survive
restarts. Everything has a sensible default, and unknown keys are ignored so
config files stay forward-compatible.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


CONFIG_DIR = Path.home() / ".healthpals"
CONFIG_FILE = CONFIG_DIR / "config.json"


# Notification "loudness" profiles.
PROFILE_HIGH = "high"   # cute animated popup near the tray
PROFILE_LOW = "low"     # native Windows / system tray notification


@dataclass
class Config:
    """All user-tunable settings."""

    # --- General ---
    companion: str = "bulldee"          # active mascot id
    notification_profile: str = PROFILE_HIGH
    autostart: bool = False
    play_sounds: bool = True
    custom_sound_path: str = ""        # optional path to custom audio file (.wav, .mp3, etc.)
    first_run: bool = True
    # What the window's X button does: "ask", "quit", or "tray".
    close_behavior: str = "ask"

    # --- Active hours (only nudge you during the working day) ---
    active_hours_enabled: bool = True
    active_start: str = "09:00"         # HH:MM 24h
    active_end: str = "18:00"
    # Days of week the app is active. 0 = Monday .. 6 = Sunday.
    active_days: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])

    # --- Reminder behaviour ---
    # Global multiplier on every reminder interval (1.0 = as configured).
    # Lower = more frequent, higher = calmer.
    frequency_scale: float = 1.0
    # Per-reminder overrides: {reminder_id: {"enabled": bool, "interval_min": int}}
    reminder_overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    # User-defined reminders: [{"id","title","emoji","interval_min","messages"?}]
    custom_reminders: list[dict[str, Any]] = field(default_factory=list)
    # Snooze length in minutes when you tap "later".
    snooze_minutes: int = 10
    paused: bool = False

    # --- Pomodoro / focus ---
    pomodoro_focus_min: int = 25
    pomodoro_short_break_min: int = 5
    pomodoro_long_break_min: int = 15
    pomodoro_rounds: int = 4            # focus rounds before a long break
    pomodoro_auto_start_breaks: bool = True
    pomodoro_pause_reminders: bool = True  # hush health nudges while focusing

    # --- Window state ---
    window_pos: list[int] | None = None

    # ------------------------------------------------------------------ #
    # Persistence helpers
    # ------------------------------------------------------------------ #
    @classmethod
    def load(cls) -> "Config":
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        else:
            data = {}

        cfg = cls()
        valid = {f for f in cfg.__dataclass_fields__}  # type: ignore[attr-defined]
        for key, value in data.items():
            if key in valid:
                setattr(cfg, key, value)
        return cfg

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps(asdict(self), indent=2), encoding="utf-8"
        )

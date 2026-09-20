"""Reminder scheduling engine.

Design goals (kept deliberately simple):
- One low-frequency QTimer drives everything (ticks every ~15s). No threads,
  no busy-waiting, negligible CPU.
- Each enabled reminder tracks its own "next due" monotonic timestamp.
- Active-hours, pause and pomodoro-hush are checked at fire time so state
  changes take effect immediately without rescheduling gymnastics.
"""
from __future__ import annotations

import random
import time
from datetime import datetime, time as dtime

from PySide6.QtCore import QObject, QTimer, Signal

from .config import Config
from .models import build_reminders_map, Reminder

# How often the engine wakes to check what's due. Coarse on purpose.
_TICK_MS = 15_000


def _parse_hhmm(value: str, fallback: dtime) -> dtime:
    try:
        hh, mm = value.split(":")
        return dtime(int(hh), int(mm))
    except (ValueError, AttributeError):
        return fallback


class ReminderScheduler(QObject):
    """Fires `reminder_due` when a health nudge should be shown."""

    reminder_due = Signal(object)  # emits a Reminder

    def __init__(self, config: Config, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._next_due: dict[str, float] = {}
        self._reminders: dict[str, Reminder] = {}
        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_MS)
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        self.reschedule_all()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def reschedule_all(self) -> None:
        """Recompute next-due times for every reminder from current config."""
        self._reminders = build_reminders_map(self._config.custom_reminders)
        now = time.monotonic()
        self._next_due = {
            rid: now + self._interval_seconds(reminder)
            for rid, reminder in self._reminders.items()
            if self._is_enabled(rid)
        }

    def snooze(self, reminder_id: str) -> None:
        minutes = max(1, self._config.snooze_minutes)
        self._next_due[reminder_id] = time.monotonic() + minutes * 60

    def mark_done(self, reminder_id: str) -> None:
        """Reset a reminder's cycle after it's acted on or dismissed."""
        reminder = self._reminders.get(reminder_id)
        if reminder is not None:
            self._next_due[reminder_id] = (
                time.monotonic() + self._interval_seconds(reminder)
            )

    def enabled_reminders(self) -> list[Reminder]:
        """All currently-enabled reminders (built-in + custom)."""
        return [r for rid, r in self._reminders.items() if self._is_enabled(rid)]

    def next_up(self) -> tuple[Reminder, float] | None:
        """Return the soonest reminder and seconds until it fires."""
        soonest: tuple[Reminder, float] | None = None
        now = time.monotonic()
        for rid, due in self._next_due.items():
            reminder = self._reminders.get(rid)
            if reminder is None:
                continue
            remaining = due - now
            if soonest is None or remaining < soonest[1]:
                soonest = (reminder, remaining)
        return soonest

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _tick(self) -> None:
        if self._config.paused or not self._within_active_window():
            return

        now = time.monotonic()
        # Fire at most one reminder per tick so nudges never pile up.
        due_now = [rid for rid, due in self._next_due.items() if due <= now]
        if not due_now:
            return

        rid = random.choice(due_now)
        reminder = self._reminders.get(rid)
        self.mark_done(rid)  # reschedule regardless of what the UI does
        if reminder is not None:
            self.reminder_due.emit(reminder)

    def _interval_seconds(self, reminder: Reminder) -> float:
        override = self._config.reminder_overrides.get(reminder.id, {})
        minutes = override.get("interval_min", reminder.default_interval_min)
        scale = max(0.25, float(self._config.frequency_scale))
        return max(60.0, minutes * 60 * scale)

    def _is_enabled(self, reminder_id: str) -> bool:
        override = self._config.reminder_overrides.get(reminder_id)
        if override is not None and "enabled" in override:
            return bool(override["enabled"])
        reminder = self._reminders.get(reminder_id)
        return reminder.enabled_by_default if reminder is not None else True

    def _within_active_window(self) -> bool:
        cfg = self._config
        if not cfg.active_hours_enabled:
            return True
        now = datetime.now()
        if now.weekday() not in cfg.active_days:
            return False
        start = _parse_hhmm(cfg.active_start, dtime(9, 0))
        end = _parse_hhmm(cfg.active_end, dtime(18, 0))
        current = now.time()
        if start <= end:
            return start <= current <= end
        # Overnight window (e.g. 22:00–06:00).
        return current >= start or current <= end

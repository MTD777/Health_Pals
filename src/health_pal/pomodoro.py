"""Pomodoro / focus timer.

A tiny state machine driven by a single 1-second QTimer. It knows nothing
about the UI — it just emits signals the widgets subscribe to. This keeps the
timer logic testable and the UI dumb.
"""
from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QObject, QTimer, Signal

from .config import Config


class Phase(Enum):
    IDLE = "idle"
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


_LABELS = {
    Phase.IDLE: "Ready",
    Phase.FOCUS: "Focus",
    Phase.SHORT_BREAK: "Short break",
    Phase.LONG_BREAK: "Long break",
}


class PomodoroTimer(QObject):
    """Focus/break cycle timer."""

    tick = Signal(int, int)          # remaining_seconds, total_seconds
    phase_changed = Signal(object)   # Phase
    round_completed = Signal(int)    # completed focus rounds so far
    finished_cycle = Signal(object)  # Phase that just ended

    def __init__(self, config: Config, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._phase = Phase.IDLE
        self._remaining = 0
        self._total = 0
        self._completed_focus = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_second)

    # ------------------------------------------------------------------ #
    # Public state
    # ------------------------------------------------------------------ #
    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def is_running(self) -> bool:
        return self._timer.isActive()

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def total(self) -> int:
        return self._total

    @property
    def completed_focus(self) -> int:
        return self._completed_focus

    @staticmethod
    def label_for(phase: Phase) -> str:
        return _LABELS[phase]

    # ------------------------------------------------------------------ #
    # Controls
    # ------------------------------------------------------------------ #
    def start_focus(self) -> None:
        self._begin(Phase.FOCUS, self._config.pomodoro_focus_min)

    def start_break(self) -> None:
        long_every = max(1, self._config.pomodoro_rounds)
        if self._completed_focus > 0 and self._completed_focus % long_every == 0:
            self._begin(Phase.LONG_BREAK, self._config.pomodoro_long_break_min)
        else:
            self._begin(Phase.SHORT_BREAK, self._config.pomodoro_short_break_min)

    def toggle_pause(self) -> None:
        if self._phase == Phase.IDLE:
            self.start_focus()
        elif self._timer.isActive():
            self._timer.stop()
        else:
            self._timer.start()

    def reset(self) -> None:
        self._timer.stop()
        self._completed_focus = 0
        self._set_phase(Phase.IDLE)
        self._remaining = 0
        self._total = 0
        self.tick.emit(0, 0)

    def skip(self) -> None:
        """Jump straight to the end of the current phase."""
        if self._phase != Phase.IDLE:
            self._remaining = 0
            self._on_second()

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _begin(self, phase: Phase, minutes: int) -> None:
        self._set_phase(phase)
        self._total = max(1, minutes) * 60
        self._remaining = self._total
        self.tick.emit(self._remaining, self._total)
        self._timer.start()

    def _set_phase(self, phase: Phase) -> None:
        if phase != self._phase:
            self._phase = phase
            self.phase_changed.emit(phase)

    def _on_second(self) -> None:
        self._remaining -= 1
        if self._remaining > 0:
            self.tick.emit(self._remaining, self._total)
            return

        self._timer.stop()
        self.tick.emit(0, self._total)
        ended = self._phase

        if ended == Phase.FOCUS:
            self._completed_focus += 1
            self.round_completed.emit(self._completed_focus)

        self.finished_cycle.emit(ended)

        # Decide what comes next.
        if ended == Phase.FOCUS:
            if self._config.pomodoro_auto_start_breaks:
                self.start_break()
            else:
                self._set_phase(Phase.IDLE)
        else:
            # A break ended — return to idle; user starts the next focus block.
            self._set_phase(Phase.IDLE)

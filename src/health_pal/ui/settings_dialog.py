"""Settings dialog.

Groups all tunables into a scrollable form. Saving writes config to disk and
emits `settings_saved` so the running app can apply changes immediately.
"""
from __future__ import annotations

import uuid

from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from .. import autostart
from ..config import PROFILE_HIGH, PROFILE_LOW, Config
from ..mascots import MASCOTS
from ..models import DEFAULT_REMINDERS
from .theme import DIALOG_STYLE, GHOST_BUTTON, PRIMARY_BUTTON, Palette, app_font

_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# A friendly starter palette of emoji for custom reminders.
_EMOJI_CHOICES = [
    "⭐", "💪", "🧘", "🚶", "💧", "👀", "🪑", "🙆", "🧍", "🤸",
    "☕", "🍎", "📵", "🌿", "🎧", "📖", "🧠", "❤️", "🐾", "🔔",
]


class SettingsDialog(QDialog):
    settings_saved = Signal()

    def __init__(self, config: Config, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle("HealthPals — Settings")
        self.setMinimumSize(460, 560)
        self.setStyleSheet(DIALOG_STYLE)

        self._reminder_rows: dict[str, tuple[QCheckBox, QSpinBox]] = {}
        # Custom rows: list of dicts {id, title, emoji, check, spin, widget}.
        self._custom_rows: list[dict] = []
        self._day_boxes: list[QCheckBox] = []

        self._build_ui()
        self._load_from_config()

    # ------------------------------------------------------------------ #
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        layout.addWidget(self._general_group())
        layout.addWidget(self._active_hours_group())
        layout.addWidget(self._reminders_group())
        layout.addWidget(self._pomodoro_group())
        layout.addStretch(1)

        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        footer = QHBoxLayout()
        footer.setContentsMargins(20, 12, 20, 16)
        footer.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(GHOST_BUTTON)
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save")
        save.setStyleSheet(PRIMARY_BUTTON)
        save.clicked.connect(self._on_save)
        footer.addWidget(cancel)
        footer.addWidget(save)
        root.addLayout(footer)

    def _group(self, title: str) -> QGroupBox:
        box = QGroupBox(title)
        box.setFont(app_font(11, bold=True))
        return box

    # ------------------------------------------------------------------ #
    def _general_group(self) -> QGroupBox:
        box = self._group("General")
        form = QFormLayout(box)
        form.setSpacing(10)

        self._profile_combo = QComboBox()
        self._profile_combo.addItem("Cute popup card", PROFILE_HIGH)
        self._profile_combo.addItem("Windows notification (system tray)", PROFILE_LOW)
        form.addRow("Reminder style", self._profile_combo)

        self._companion_combo = QComboBox()
        for mascot_id, cls in MASCOTS.items():
            self._companion_combo.addItem(cls.display_name, mascot_id)
        form.addRow("Companion", self._companion_combo)

        self._autostart_box = QCheckBox()
        self._bind_toggle(self._autostart_box, "Launch at login")
        form.addRow("Startup", self._autostart_box)

        self._sounds_box = QCheckBox()
        self._bind_toggle(self._sounds_box, "Play notification sound")
        form.addRow("Sound", self._sounds_box)

        # Custom sound selector row
        sound_row = QHBoxLayout()
        sound_row.setSpacing(6)
        self._sound_path_edit = QLineEdit()
        self._sound_path_edit.setPlaceholderText("Default chime (or select custom file)")
        self._sound_path_edit.setReadOnly(True)

        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet(GHOST_BUTTON)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_custom_sound)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(GHOST_BUTTON)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self._sound_path_edit.clear())

        test_sound_btn = QPushButton("Test 🔊")
        test_sound_btn.setStyleSheet(GHOST_BUTTON)
        test_sound_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_sound_btn.clicked.connect(self._test_current_sound)

        sound_row.addWidget(self._sound_path_edit, stretch=1)
        sound_row.addWidget(browse_btn)
        sound_row.addWidget(clear_btn)
        sound_row.addWidget(test_sound_btn)

        sound_wrap = QWidget()
        sound_wrap.setLayout(sound_row)
        form.addRow("Custom sound", sound_wrap)

        self._freq_slider = QSlider(Qt.Orientation.Horizontal)
        self._freq_slider.setMinimum(50)   # 0.5x  (more frequent)
        self._freq_slider.setMaximum(200)  # 2.0x  (calmer)
        self._freq_label = QLabel()
        self._freq_slider.valueChanged.connect(self._update_freq_label)
        freq_row = QHBoxLayout()
        freq_row.addWidget(self._freq_slider)
        freq_row.addWidget(self._freq_label)
        freq_wrap = QWidget()
        freq_wrap.setLayout(freq_row)
        form.addRow("Overall pace", freq_wrap)

        self._snooze_spin = QSpinBox()
        self._snooze_spin.setRange(1, 60)
        self._snooze_spin.setSuffix(" min")
        form.addRow("Snooze length", self._snooze_spin)
        return box

    def _active_hours_group(self) -> QGroupBox:
        box = self._group("Active hours")
        layout = QVBoxLayout(box)

        self._active_enabled = QCheckBox()
        self._bind_toggle(self._active_enabled, "Only nudge during working hours")
        layout.addWidget(self._active_enabled)

        times = QHBoxLayout()
        self._start_time = QTimeEdit()
        self._start_time.setDisplayFormat("HH:mm")
        self._end_time = QTimeEdit()
        self._end_time.setDisplayFormat("HH:mm")
        times.addWidget(QLabel("From"))
        times.addWidget(self._start_time)
        times.addWidget(QLabel("to"))
        times.addWidget(self._end_time)
        times.addStretch(1)
        layout.addLayout(times)

        days = QHBoxLayout()
        for i, name in enumerate(_DAY_NAMES):
            cb = QCheckBox()
            self._bind_toggle(cb, name)
            self._day_boxes.append(cb)
            days.addWidget(cb)
        layout.addLayout(days)
        return box

    def _reminders_group(self) -> QGroupBox:
        box = self._group("Reminders")
        outer = QVBoxLayout(box)
        outer.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(8)
        for reminder in DEFAULT_REMINDERS:
            check = QCheckBox()
            self._bind_toggle(check, f"{reminder.emoji} {reminder.title}")
            spin = QSpinBox()
            spin.setRange(1, 240)
            spin.setSuffix(" min")
            form.addRow(self._reminder_row_widget(check, spin))
            self._reminder_rows[reminder.id] = (check, spin)
        outer.addLayout(form)

        # Dynamic container for user-defined reminders.
        self._custom_container = QVBoxLayout()
        self._custom_container.setSpacing(8)
        outer.addLayout(self._custom_container)

        add_btn = QPushButton("＋  Add custom reminder")
        add_btn.setStyleSheet(GHOST_BUTTON)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._open_add_dialog)

        restore_btn = QPushButton("↺  Restore defaults")
        restore_btn.setStyleSheet(GHOST_BUTTON)
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.clicked.connect(self._restore_defaults)

        buttons = QHBoxLayout()
        buttons.addWidget(add_btn)
        buttons.addWidget(restore_btn)
        outer.addLayout(buttons)
        return box

    def _restore_defaults(self) -> None:
        """Reset built-in reminders to the recommended on/off + intervals."""
        for reminder in DEFAULT_REMINDERS:
            check, spin = self._reminder_rows[reminder.id]
            check.setChecked(reminder.enabled_by_default)
            spin.setValue(reminder.default_interval_min)

    @staticmethod
    def _reminder_row_widget(check: QCheckBox, spin: QSpinBox) -> QWidget:
        row = QHBoxLayout()
        row.addWidget(check, stretch=1)
        row.addWidget(QLabel("every"))
        row.addWidget(spin)
        wrap = QWidget()
        wrap.setLayout(row)
        return wrap

    # ------------------------------------------------------------------ #
    # Custom reminders
    # ------------------------------------------------------------------ #
    def _add_custom_row(self, data: dict) -> None:
        rid = data["id"]
        override = self._config.reminder_overrides.get(rid, {})

        # Glyph-only enable toggle (name lives in its own wrapping label so
        # long names wrap instead of overflowing).
        check = QCheckBox()
        self._bind_toggle(check, "")
        check.setChecked(override.get("enabled", data.get("enabled", True)))

        name_lbl = QLabel(f"{data.get('emoji', '⭐')} {data['title']}")
        name_lbl.setWordWrap(True)

        # Keep the name label visually consistent with the built-in toggles
        # (same green/grey + size), syncing colour with the enable state.
        def _sync_name(checked: bool) -> None:
            color = "#2E9E6B" if checked else "#9A8A7C"
            weight = "600" if checked else "500"
            name_lbl.setStyleSheet(
                f"color: {color}; font-weight: {weight}; font-size: 13px;"
            )

        _sync_name(check.isChecked())
        check.toggled.connect(_sync_name)

        spin = QSpinBox()
        spin.setRange(1, 240)
        spin.setSuffix(" min")
        spin.setValue(override.get("interval_min", data.get("interval_min", 30)))

        compact = (
            "QPushButton { background: transparent; color: #8A7A6D;"
            " border: 2px solid #E9D4B8; border-radius: 10px; padding: 3px 10px; }"
            " QPushButton:hover { background: #F3E4CF; color: #4A3B32; }"
        )
        edit = QPushButton("Edit")
        edit.setStyleSheet(compact)
        edit.setCursor(Qt.CursorShape.PointingHandCursor)
        remove = QPushButton("Remove")
        remove.setStyleSheet(compact)
        remove.setCursor(Qt.CursorShape.PointingHandCursor)

        grid = QGridLayout()
        grid.setContentsMargins(2, 2, 2, 2)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        top = Qt.AlignmentFlag.AlignTop
        grid.addWidget(check, 0, 0, top)
        grid.addWidget(name_lbl, 0, 1)
        grid.addWidget(QLabel("every"), 0, 2, top)
        grid.addWidget(spin, 0, 3, top)
        grid.addWidget(edit, 0, 4, top)
        grid.addWidget(remove, 0, 5, top)
        grid.setColumnStretch(1, 1)
        wrap = QFrame()
        wrap.setLayout(grid)
        self._custom_container.addWidget(wrap)

        entry = {
            "id": rid,
            "title": data["title"],
            "emoji": data.get("emoji", "⭐"),
            "messages": data.get("messages"),
            "check": check,
            "spin": spin,
            "name_lbl": name_lbl,
            "widget": wrap,
        }
        self._custom_rows.append(entry)
        remove.clicked.connect(lambda: self._remove_custom_row(entry))
        edit.clicked.connect(lambda: self._edit_custom_row(entry))

    def _edit_custom_row(self, entry: dict) -> None:
        dialog = AddReminderDialog(
            self,
            title="Edit custom reminder",
            initial=(entry["title"], entry["emoji"], entry["spin"].value()),
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, emoji, interval = dialog.result_values()
            entry["title"] = title
            entry["emoji"] = emoji
            entry["messages"] = None  # regenerate lines from the new name
            entry["spin"].setValue(interval)
            entry["name_lbl"].setText(f"{emoji} {title}")

    def _remove_custom_row(self, entry: dict) -> None:
        entry["widget"].setParent(None)
        entry["widget"].deleteLater()
        if entry in self._custom_rows:
            self._custom_rows.remove(entry)

    def _open_add_dialog(self) -> None:
        dialog = AddReminderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, emoji, interval = dialog.result_values()
            self._add_custom_row(
                {
                    "id": "custom_" + uuid.uuid4().hex[:8],
                    "title": title,
                    "emoji": emoji,
                    "interval_min": interval,
                    "enabled": True,
                }
            )

    def _pomodoro_group(self) -> QGroupBox:
        box = self._group("Focus timer")
        form = QFormLayout(box)
        form.setSpacing(10)

        self._focus_spin = self._minutes_spin(1, 120)
        self._short_spin = self._minutes_spin(1, 60)
        self._long_spin = self._minutes_spin(1, 60)
        self._rounds_spin = QSpinBox()
        self._rounds_spin.setRange(1, 12)
        self._auto_breaks = QCheckBox()
        self._bind_toggle(self._auto_breaks, "Auto-start breaks after focus")
        self._hush = QCheckBox()
        self._bind_toggle(self._hush, "Pause health nudges while focusing")

        form.addRow("Focus length", self._focus_spin)
        form.addRow("Short break", self._short_spin)
        form.addRow("Long break", self._long_spin)
        form.addRow("Rounds before long break", self._rounds_spin)
        form.addRow("", self._auto_breaks)
        form.addRow("", self._hush)
        return box

    @staticmethod
    def _minutes_spin(lo: int, hi: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(lo, hi)
        spin.setSuffix(" min")
        return spin

    @staticmethod
    def _bind_toggle(cb: QCheckBox, label: str) -> None:
        """Show a clear ☑ (enabled) / ☐ (disabled) glyph and colour."""

        def update(checked: bool) -> None:
            glyph = "☑" if checked else "☐"
            cb.setText(f"{glyph}  {label}")
            color = "#2E9E6B" if checked else "#8A7A6D"
            weight = "600" if checked else "500"
            cb.setStyleSheet(
                f"QCheckBox {{ color: {color}; font-weight: {weight};"
                " font-size: 13px; spacing: 8px; background: transparent; }"
                " QCheckBox::indicator { width: 0px; height: 0px; }"
            )

        update(cb.isChecked())
        cb.toggled.connect(update)

    def _update_freq_label(self, value: int) -> None:
        self._freq_label.setText(f"{value / 100:.2f}×")

    def _browse_custom_sound(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Custom Sound File",
            "",
            "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a);;All Files (*)",
        )
        if file_path:
            self._sound_path_edit.setText(file_path)

    def _test_current_sound(self) -> None:
        from ..sound import Chime

        path = self._sound_path_edit.text().strip()
        chime = Chime()
        chime.play(custom_path_override=path)

    # ------------------------------------------------------------------ #
    def _load_from_config(self) -> None:
        c = self._config
        idx = self._profile_combo.findData(c.notification_profile)
        self._profile_combo.setCurrentIndex(max(0, idx))
        cidx = self._companion_combo.findData(c.companion)
        self._companion_combo.setCurrentIndex(max(0, cidx))
        self._autostart_box.setChecked(autostart.is_autostart_enabled())
        self._sounds_box.setChecked(c.play_sounds)
        self._sound_path_edit.setText(c.custom_sound_path)
        self._freq_slider.setValue(int(c.frequency_scale * 100))
        self._update_freq_label(self._freq_slider.value())
        self._snooze_spin.setValue(c.snooze_minutes)

        self._active_enabled.setChecked(c.active_hours_enabled)
        self._start_time.setTime(QTime.fromString(c.active_start, "HH:mm"))
        self._end_time.setTime(QTime.fromString(c.active_end, "HH:mm"))
        for i, cb in enumerate(self._day_boxes):
            cb.setChecked(i in c.active_days)

        for rid, (check, spin) in self._reminder_rows.items():
            override = c.reminder_overrides.get(rid, {})
            reminder = next(r for r in DEFAULT_REMINDERS if r.id == rid)
            check.setChecked(override.get("enabled", reminder.enabled_by_default))
            spin.setValue(override.get("interval_min", reminder.default_interval_min))

        # Populate user-defined reminders.
        for data in c.custom_reminders:
            self._add_custom_row(data)

        self._focus_spin.setValue(c.pomodoro_focus_min)
        self._short_spin.setValue(c.pomodoro_short_break_min)
        self._long_spin.setValue(c.pomodoro_long_break_min)
        self._rounds_spin.setValue(c.pomodoro_rounds)
        self._auto_breaks.setChecked(c.pomodoro_auto_start_breaks)
        self._hush.setChecked(c.pomodoro_pause_reminders)

    def _on_save(self) -> None:
        c = self._config
        c.notification_profile = self._profile_combo.currentData()
        c.companion = self._companion_combo.currentData()
        c.play_sounds = self._sounds_box.isChecked()
        c.custom_sound_path = self._sound_path_edit.text().strip()
        c.frequency_scale = self._freq_slider.value() / 100
        c.snooze_minutes = self._snooze_spin.value()

        c.active_hours_enabled = self._active_enabled.isChecked()
        c.active_start = self._start_time.time().toString("HH:mm")
        c.active_end = self._end_time.time().toString("HH:mm")
        c.active_days = [i for i, cb in enumerate(self._day_boxes) if cb.isChecked()]

        overrides: dict[str, dict] = {}
        for rid, (check, spin) in self._reminder_rows.items():
            overrides[rid] = {
                "enabled": check.isChecked(),
                "interval_min": spin.value(),
            }
        # Persist custom reminders + their enabled/interval overrides.
        customs: list[dict] = []
        for entry in self._custom_rows:
            customs.append(
                {
                    "id": entry["id"],
                    "title": entry["title"],
                    "emoji": entry["emoji"],
                    "messages": entry["messages"],
                    "interval_min": entry["spin"].value(),
                }
            )
            overrides[entry["id"]] = {
                "enabled": entry["check"].isChecked(),
                "interval_min": entry["spin"].value(),
            }
        c.custom_reminders = customs
        c.reminder_overrides = overrides

        c.pomodoro_focus_min = self._focus_spin.value()
        c.pomodoro_short_break_min = self._short_spin.value()
        c.pomodoro_long_break_min = self._long_spin.value()
        c.pomodoro_rounds = self._rounds_spin.value()
        c.pomodoro_auto_start_breaks = self._auto_breaks.isChecked()
        c.pomodoro_pause_reminders = self._hush.isChecked()

        # Apply autostart change (best-effort; ignores failure).
        desired = self._autostart_box.isChecked()
        if desired != autostart.is_autostart_enabled():
            autostart.set_autostart(desired)
        c.autostart = autostart.is_autostart_enabled()

        c.save()
        self.settings_saved.emit()
        self.accept()


class AddReminderDialog(QDialog):
    """Small dialog to create or edit a custom reminder."""

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "New custom reminder",
        initial: tuple[str, str, int] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(340)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. Refill snacks")
        self._name.setMaxLength(40)
        form.addRow("Name", self._name)

        self._emoji = QComboBox()
        self._emoji.setEditable(True)
        self._emoji.addItems(_EMOJI_CHOICES)
        self._emoji.setMaxVisibleItems(10)
        form.addRow("Emoji", self._emoji)

        self._interval = QSpinBox()
        self._interval.setRange(1, 240)
        self._interval.setSuffix(" min")
        self._interval.setValue(30)
        form.addRow("Every", self._interval)
        layout.addLayout(form)

        if initial is not None:
            self._name.setText(initial[0])
            self._emoji.setCurrentText(initial[1])
            self._interval.setValue(initial[2])

        self._error = QLabel("")
        self._error.setStyleSheet("color: #E06666;")
        self._error.setFont(app_font(9))
        layout.addWidget(self._error)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setStyleSheet(GHOST_BUTTON)
        cancel.clicked.connect(self.reject)
        add = QPushButton("Add")
        add.setStyleSheet(PRIMARY_BUTTON)
        add.clicked.connect(self._validate_accept)
        buttons.addWidget(cancel)
        buttons.addWidget(add)
        layout.addLayout(buttons)

        self._name.setFocus()

    def _validate_accept(self) -> None:
        if not self._name.text().strip():
            self._error.setText("Please give your reminder a name.")
            return
        self.accept()

    def result_values(self) -> tuple[str, str, int]:
        title = self._name.text().strip()
        emoji = self._emoji.currentText().strip() or "⭐"
        # Keep just the first grapheme in case the user typed extra text.
        emoji = emoji.split()[0][:2] if emoji else "⭐"
        return title, emoji, self._interval.value()

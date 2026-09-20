# CLAUDE.md — Project guide for HealthPals 🐾

This file orients humans **and** AI agents working on this repository. Read it
before making changes. It explains what the app is, how it's structured, how to
run and test it, the conventions to follow, and where to extend safely.

---

## 1. What this project is

**HealthPals** is a cute, self-contained **desktop health companion** for
Windows (works cross-platform where a system tray exists). A friendly animated
mascot lives in the system tray and gently reminds the user to move, stretch,
hydrate, rest their eyes, and stay focused during the working day. It also
includes a Pomodoro-style focus timer.

- **First companion:** **Bull-dee**, a brown-and-white bulldog with
  heterochromia (one blue eye, one brown eye).
- **Second companion:** **Kuji**, a blue whale.
- Everything visual (mascots, tray icon) is **drawn in code with QPainter** —
  there are **no bundled image assets** required for the mascots.

### Objectives / design goals
1. **Purposeful, not annoying.** Gentle nudges with sensible defaults; the user
   is always in control (intervals, active hours, pause, enable/disable).
2. **Two notification styles:** an animated popup card and a default **Windows/system tray notification**.
3. **Simple, secure, performant** (see §7). No network, no telemetry, minimal
   dependencies.
4. **Extensible:** adding a reminder or a companion is a small, local change.

---

## 2. Tech stack

- **Language:** Python 3.10+ (developed/tested on 3.14).
- **GUI:** PySide6 (Qt for Python, LGPL). The only runtime dependency.
- **Persistence:** a single JSON file at `~/.healthpals/config.json`.
- **Audio:** a synthesized WAV chime cached at `~/.healthpals/chime.wav`,
  played via `winsound` on Windows (preferred) or `QSoundEffect` elsewhere.

---

## 3. How to run

```powershell
# from the project root
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Start-Process pythonw .\run.py     # windowless; lives in the tray
```

- On Windows prefer `pythonw` (no console window). `python run.py` also works.
- **`quickstart.bat`** provides a menu: **1** start (creates venv, installs,
  launches), **2** stop (kills only the HealthPals `run.py` process), **3** exit.
- Closing the dashboard **X** asks whether to quit or minimize to tray (with a
  "remember my choice" option). Real quit is via the tray menu or that dialog.

---

## 4. Project structure

```
run.py                     # launcher: adds src/ to path, calls health_pal.app.main
quickstart.bat             # Windows console menu to start/stop the app
requirements.txt           # PySide6 only
assets/                    # optional branding: icon.ico / icon.png (taskbar icon)
src/health_pal/
  __init__.py              # app name + version
  __main__.py              # enables `python -m health_pal`
  app.py                   # ORCHESTRATOR: owns config/scheduler/pomodoro/tray/
                           #   window/popup and wires their signals together
  config.py                # Config dataclass + JSON load/save (~/.healthpals)
  models.py                # Reminder dataclass + DEFAULT_REMINDERS + custom helpers
  scheduler.py             # ReminderScheduler: one 15s QTimer decides what's due
  pomodoro.py              # PomodoroTimer: focus/break state machine (1s QTimer)
  sound.py                 # Chime: synthesizes + plays the gentle WAV
  autostart.py             # cross-platform launch-at-login (USER scope only)
  branding.py              # window/taskbar icon + Windows AppUserModelID
  mascots/
    __init__.py            # MASCOTS registry + create_mascot()
    base.py                # Mascot base: shared 30 FPS animation + mood engine
    bulldog.py             # Bull-dee (BulldogMascot)
    whale.py               # Kuji (WhaleMascot)
  ui/
    theme.py               # Palette, fonts, reusable stylesheet snippets
    tray.py                # HealthTray: system tray icon + menu + system notification notify()
    reminder_popup.py      # ReminderPopup: the high-profile animated card
    pomodoro_widget.py     # PomodoroWidget: the circular focus ring
    main_window.py         # MainWindow: the dashboard
    settings_dialog.py     # SettingsDialog + AddReminderDialog (custom reminders)
```

---

## 5. Architecture & data flow

- **`app.py` is the switchboard.** It constructs the long-lived objects and
  connects Qt signals. Components stay decoupled and know nothing about each
  other — they emit signals; `app.py` decides what happens.
- **Scheduling:** `ReminderScheduler` keeps a `{reminder_id: next_due}` map and a
  single low-frequency `QTimer` (~15s). On each tick it fires **at most one** due
  reminder (`reminder_due` signal), respecting active hours and pause. Custom
  reminders are merged in via `models.build_reminders_map(config.custom_reminders)`.
- **Presenting a reminder:** `app._show_reminder()` either shows the popup
  card or a system tray notification (`notify()`), then plays the chime.
  **Popups are queued** — only one shows at a time; overlapping reminders wait
  (`_popup_queue` + the popup's `dismissed` signal) to avoid a race where a
  popup could get stuck.
- **Pomodoro** is independent; it can optionally **hush** health nudges while a
  focus block is running (`_reminders_hushed`).
- **Companions** are self-animating `QWidget`s. Changing the companion in
  Settings applies live to the window, popup, and tray icon via `set_companion`.

### Key config fields (`config.py`)
`companion`, `notification_profile` (`high`/`low`), `autostart`, `play_sounds`,
`active_hours_enabled` + `active_start/end/days`, `frequency_scale`,
`reminder_overrides` (`{id: {enabled, interval_min}}`), `custom_reminders`,
`snooze_minutes`, `paused`, the `pomodoro_*` settings, and `close_behavior`
(`ask`/`quit`/`tray`).

---

## 6. Common tasks (how to extend)

### Add a built-in reminder
Add one `Reminder(...)` entry to `DEFAULT_REMINDERS` in `models.py`. Set
`enabled_by_default=False` for optional/intense ones. Messages may contain the
`{pal}` placeholder, which is replaced with the active companion's name at
display time. That's it — the scheduler, settings UI, and popups pick it up.

### Add a new companion (mascot)
1. Create `src/health_pal/mascots/<name>.py` with a subclass of `Mascot`
   implementing `paint_mascot(painter, rect)`. Set `mascot_id` and
   `display_name`. Reuse the shared moods: `idle`, `wave`, `cheer`, `stretch`,
   `walk`, `drink`, `eyes` (see `bulldog.py`/`whale.py` for patterns:
   `self.phase`, `self.blink_amount()`, `self.breathe()`).
2. Register it in `mascots/__init__.py`'s `MASCOTS` dict.
   The companion dropdown, dashboard, popup, and tray icon update automatically.

### Custom reminders (user-facing)
Handled entirely in `settings_dialog.py` (`AddReminderDialog`) and persisted in
`config.custom_reminders`. Each has `id`, `title`, `emoji`, `interval_min`, and
optional `messages`.

### Building a Standalone .exe
Run `pyinstaller HealthPals.spec` (or select option **[3]** in `quickstart.bat`). The standalone windowless executable is output to `dist/HealthPals.exe`.
`autostart.py` automatically detects when running from a frozen executable (`sys.frozen`) and registers `HealthPals.exe` directly in the user startup registry.

---

## 7. Conventions & principles (follow these)

- **Simplicity first.** One low-frequency timer drives reminders; the Pomodoro
  uses one 1-second timer. No threads, no polling/busy loops. Animation timers
  (30 FPS) run **only while a widget is visible** to keep idle CPU near zero.
- **Security & privacy.** No network calls, no telemetry, no `eval`. Config is
  plain JSON in the user's home dir. Autostart writes **user-scoped** entries
  only (registry Run key / LaunchAgent / XDG autostart) — no admin/root, easily
  reversible, paths are quoted.
- **UI/logic separation.** Timers/state machines (`scheduler.py`, `pomodoro.py`)
  contain no UI; widgets are presentational and communicate via signals.
- **Styling** lives in `ui/theme.py` (`Palette`, `app_font`, button snippets).
  Reuse it; don't hardcode colors elsewhere.
- **Don't over-engineer.** Make the change requested; avoid speculative
  abstractions, and don't add comments/annotations to untouched code.

---

## 8. Testing / verifying changes

There is no formal test suite yet. Validate changes with a **headless smoke
test** using Qt's offscreen platform (constructs widgets without a display):

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); \
from PySide6.QtWidgets import QApplication; app=QApplication([]); \
from health_pal.config import Config; from health_pal.scheduler import ReminderScheduler; \
from health_pal.pomodoro import PomodoroTimer; from health_pal.ui.main_window import MainWindow; \
c=Config(); s=ReminderScheduler(c); s.start(); w=MainWindow(c,s,PomodoroTimer(c)); w.show(); \
print('OK')"
```

Notes:
- A `QFontDatabase: Cannot find font directory` warning under offscreen is
  harmless (real desktop uses system fonts).
- To exercise paint code, `show()` the widget and pump the event loop briefly.
- To visually check a mascot, render it to a PNG (`mascot.render_icon(size)` or
  `paint_mascot` onto a `QPixmap`) and inspect it, then delete the temp file.

Always run `get_errors` / your linter on edited files before finishing.

---

## 9. Operational notes & gotchas

- **Quitting:** the app sets `setQuitOnLastWindowClosed(False)` and hides to
  tray. Real quit goes through the tray menu or the close dialog → `_quit()`.
  When stopping via script, kill only the HealthPals process:
  ```powershell
  Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" |
    Where-Object { $_.CommandLine -like '*run.py*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
  ```
  (A GUI quit **saves config**; a hard kill does not — relevant if you edit
  `config.json` externally while the app runs.)
- **Sound off?** Check `play_sounds` in `~/.healthpals/config.json` and the
  "Play a soft chime" toggle in Settings. The chime WAV regenerates if deleted.
- **Ctrl+C** in a foreground `python run.py` may print a `KeyboardInterrupt`
  traceback because Qt's loop doesn't handle SIGINT cleanly — harmless.
- Config is **forward-compatible**: unknown keys are ignored on load; new fields
  get defaults.

---

## 10. Quick reference

| I want to… | Go to |
|---|---|
| Change how reminders are scheduled | `scheduler.py` |
| Add/edit a built-in reminder | `models.py` (`DEFAULT_REMINDERS`) |
| Add a new companion | `mascots/` + `mascots/__init__.py` |
| Tune the popup look/behavior | `ui/reminder_popup.py` |
| Adjust settings UI / custom reminders | `ui/settings_dialog.py` |
| Change colors/fonts | `ui/theme.py` |
| Wire new app behavior | `app.py` |
| Taskbar icon | `assets/` + `branding.py` |

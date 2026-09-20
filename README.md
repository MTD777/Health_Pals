# HealthPals 🐾

**HealthPals** is an open-source desktop health and break reminder app that lives in your system tray. It features animated companions such as **Biscuit** 🐶 (a bulldog) and **Kuji** 🐋 (a blue whale) that deliver periodic reminders to stand, stretch, hydrate, and rest your eyes during work sessions.

All visual components, including the animated mascots and tray icons, are drawn programmatically in code using Qt vector primitives (`QPainter`). This keeps the app lightweight, eliminates external image asset dependencies, and ensures high-DPI scaling at any resolution.

---

## Features ✨

- **Animated companions:** Mascots feature multi-state animations (breathing, blinking, waving, stretching, and celebrating) triggered during reminders and interactions.
- **Configurable health nudges:** Includes built-in reminders for posture checks, hydration, 20-20-20 eye rest, stretching, standing desk adjustments, and short physical breaks.
- **Custom reminders:** Create, edit, or remove custom reminders with custom titles, emojis, messages, and intervals.
- **Flexible notification styles:**
  - **Animated card popup:** A rounded window slides up from the corner of the screen and auto-dismisses after a short period.
  - **Windows system notification:** Standard system tray notification balloon.
- **Integrated Pomodoro timer:** A focus timer with configurable work and break intervals. Health nudges can automatically be suppressed during active focus blocks.
- **Schedule management:** Define active working hours and days, adjust global reminder frequency, snooze incoming nudges, or pause reminders with a single click.
- **Synthesized notification sound:** Generates a soft two-note audio chime programmatically at runtime, avoiding external audio files or default system beeps. Can be muted anytime.
- **User-scoped launch at login:** Optional autostart configured strictly within user registry/config scope, requiring no administrator permissions.
- **System tray footprint:** Runs silently in the system tray when the main dashboard is closed.

---

## Getting Started 🚀

### Prerequisites
- **Python 3.10+**
- A desktop environment with system tray support (Windows, macOS, or Linux)

### Option 1: Quickstart Script (Windows) ⭐

Double-click **`quickstart.bat`** and select **1**. The script automatically creates the virtual environment, installs required dependencies, and launches HealthPals into the system tray.

### Option 2: Manual Setup

```powershell
# Clone the repository and enter the directory
cd Health_Pals

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run HealthPals (pythonw runs windowless in the background on Windows)
Start-Process pythonw .\run.py
```

### Option 3: Building Standalone Executable (`HealthPals.exe`) 📦

To build a single standalone `.exe` file for Windows without requiring Python on the target machine:

```powershell
pip install pyinstaller pillow
pyinstaller HealthPals.spec
```
The compiled executable will be saved in `dist/HealthPals.exe`. Double-click `HealthPals.exe` to run.

On first launch, the main window opens. Closing the window minimizes HealthPals to the system tray. Double-click the tray icon to reopen the dashboard or right-click for quick actions.

---

## Configuration ⚙️

Access **Settings** from the dashboard or tray menu to:

- Switch between available companions (**Biscuit** 🐶 or **Kuji** 🐋).
- Toggle between popup cards and tray notifications.
- Enable/disable individual health reminders and adjust their intervals.
- Add, edit, or delete custom user reminders.
- Configure active hours, working days, snooze duration, and global frequency scaling.
- Set Pomodoro focus/break durations and auto-start preferences.
- Toggle sound and launch-at-login settings.

### Custom Taskbar Icon (Optional)

Place an `assets/icon.png` (1024×1024) or `assets/icon.ico` file in the project directory. HealthPals will automatically load it as the taskbar and window icon on launch.

---

## Architecture Overview 🛠️

- **Framework:** Python + PySide6 (Qt for Python).
- **Storage:** Plain JSON stored at `~/.healthpals/config.json`.
- **Resource Usage:** Uses a single low-frequency timer (~15s tick) for reminder evaluation and a 1-second timer for Pomodoro updates. Animation loops (30 FPS) run strictly while a mascot widget is visible on screen, keeping idle CPU usage near zero.
- **Privacy & Security:** Fully offline application. Performs zero network calls, collects no telemetry, and contains no external executable dependencies.

For detailed architecture diagrams, component breakdowns, and developer instructions, see [CLAUDE.md](CLAUDE.md).

---

## Contributing 🤝

Contributions are welcome! Whether you want to add a new code-drawn companion, implement new health nudges, improve accessibility, or fix bugs, feel free to get involved.

### How to contribute:
1. **Add a Companion:** Subclass `Mascot` in `src/health_pal/mascots/`, implement `paint_mascot()` using `QPainter`, and register it in `mascots/__init__.py`.
2. **Improve Features or Fix Bugs:** Review existing issues or submit a Pull Request with your changes.

### Submitting a Pull Request
1. Fork the repository and create a feature branch: `git checkout -b feature/my-feature`
2. Test your changes locally (see [CLAUDE.md](CLAUDE.md) for headless testing commands).
3. Commit and push your changes.
4. Open a Pull Request on GitHub with a description of your changes.

---

## License 📜

Distributed under the [GNU General Public License v3.0 (GPLv3)](LICENSE). See `LICENSE` for details.

---

Made to keep you healthy and focused through the workday. 🐶🐋

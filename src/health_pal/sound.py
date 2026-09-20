"""A soft, calming notification chime.

We synthesise a gentle two-note bell once and cache it as a small WAV in the
config folder — no audio assets to ship, and nothing like the jarring Windows
system beep. Playback prefers QSoundEffect (so we can keep the volume low);
if that's unavailable we fall back to winsound on Windows.
"""
from __future__ import annotations

import math
import os
import struct
import wave

from pathlib import Path

from .config import CONFIG_DIR

_CHIME_FILE = CONFIG_DIR / "chime.wav"
_FRAMERATE = 44100


def _generate_chime() -> None:
    """Render a warm, mellow two-note bell to _CHIME_FILE."""
    # Two soft notes (E5 then B5) with gentle attack and long decay.
    notes = [(0.00, 659.25), (0.16, 987.77)]
    partials = [(1.0, 1.0), (2.0, 0.35), (3.0, 0.14)]  # (harmonic, gain)
    total = 1.1
    n = int(_FRAMERATE * total)

    samples = [0.0] * n
    peak = 1e-9
    for i in range(n):
        t = i / _FRAMERATE
        value = 0.0
        for start, freq in notes:
            if t < start:
                continue
            local = t - start
            attack = 1.0 - math.exp(-local / 0.006)
            decay = math.exp(-local / 0.34)
            env = attack * decay
            for harmonic, gain in partials:
                value += env * gain * math.sin(2 * math.pi * freq * harmonic * local)
        samples[i] = value
        peak = max(peak, abs(value))

    # Normalise to a comfortable, quiet level (~55% of full scale).
    scale = 0.55 / peak
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with wave.open(str(_CHIME_FILE), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(_FRAMERATE)
        frames = bytearray()
        for value in samples:
            frames += struct.pack("<h", int(max(-1.0, min(1.0, value * scale)) * 32767))
        wav.writeframes(bytes(frames))


def _ensure_chime() -> None:
    if not _CHIME_FILE.exists():
        _generate_chime()


class Chime:
    """Plays notification sound (default synthesized chime or custom audio file)."""

    def __init__(self, volume: float = 0.5, custom_path: str = "") -> None:
        self._volume = volume
        self._custom_path = custom_path
        self._player = None
        self._audio_output = None
        try:
            _ensure_chime()
        except Exception:
            pass

    def set_custom_path(self, path: str) -> None:
        self._custom_path = path

    def play(self, custom_path_override: str | None = None) -> None:
        path_to_play = (
            custom_path_override if custom_path_override is not None else self._custom_path
        )

        # Determine target file.
        target_file: Path | None = None
        if path_to_play and os.path.exists(path_to_play):
            target_file = Path(path_to_play)
        else:
            _ensure_chime()
            target_file = _CHIME_FILE

        if not target_file or not target_file.exists():
            return

        ext = target_file.suffix.lower()

        # On Windows, winsound works directly for .wav files.
        if os.name == "nt" and ext == ".wav":
            try:
                import winsound

                winsound.PlaySound(
                    str(target_file),
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
                return
            except Exception:
                pass

        # Use QtMultimedia (QMediaPlayer / QAudioOutput) for .mp3, .ogg, or fallback.
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

            if self._player is None:
                self._player = QMediaPlayer()
                self._audio_output = QAudioOutput()
                self._player.setAudioOutput(self._audio_output)

            self._audio_output.setVolume(self._volume)
            self._player.setSource(QUrl.fromLocalFile(str(target_file)))
            self._player.play()
            return
        except Exception:
            pass

        # Final fallback for Windows .wav if QtMultimedia fails.
        if os.name == "nt":
            try:
                import winsound

                winsound.PlaySound(
                    str(target_file), winsound.SND_FILENAME | winsound.SND_ASYNC
                )
            except Exception:
                pass

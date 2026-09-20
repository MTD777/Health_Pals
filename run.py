#!/usr/bin/env python3
"""HealthPals launcher.

Run this file to start the app:  python run.py
"""
import sys
from pathlib import Path

# Make the src/ layout importable without installation.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from health_pal.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

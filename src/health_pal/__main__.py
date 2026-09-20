"""Allow `python -m health_pal`."""
import sys

from .app import main

if __name__ == "__main__":
    sys.exit(main())

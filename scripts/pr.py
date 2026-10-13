#!/usr/bin/env python3
"""Standard PR Entrypoint for Kaggle Competitions.

Forwards arguments directly to create_pr.py.
"""

import sys
from pathlib import Path

# Ensure repository root is first in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Also add scripts directory to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from create_pr import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

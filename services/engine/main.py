"""Deployment entrypoint for the Fabrient FastAPI engineering service.

The canonical engineering implementation remains in engineering/app/main.py.
This thin adapter makes the implementation available from the deployment root
services/engine without duplicating engineering logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engineering.app.main import app  # noqa: E402

__all__ = ["app"]

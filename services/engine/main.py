"""Render entrypoint for the Fabrient engineering service.

The composed application is the production surface: it includes the base
engineering API plus the advanced system-identification, reporting, and
bounded-agent routes. CORS is configured at the deployment boundary so the
frontend origin is never hard-coded into engineering code.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engineering.app.composed import app  # noqa: E402

allowed = [origin.strip() for origin in os.getenv("FABRIENT_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if allowed:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        max_age=600,
    )

__all__ = ["app"]

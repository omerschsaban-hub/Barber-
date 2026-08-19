"""Fabrient engineering application package.

The real CV/sim-to-real router is attached here so both the HTTP app and the
MCP adapter share exactly the same implementation and validation gates.
"""

from .main import app
from .real_cv_sim2real import router as real_cv_sim2real_router

app.include_router(real_cv_sim2real_router)

__all__ = ["app", "real_cv_sim2real_router"]

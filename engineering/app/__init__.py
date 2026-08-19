"""Fabrient engineering application package.

The real CV/sim-to-real routers are attached here so the HTTP app and MCP
adapter share exactly the same implementation and validation gates.
"""

from .main import app
from .real_cv_sim2real import router as real_cv_sim2real_router
from .real_cv_mcp_routes import router as real_cv_mcp_router

app.include_router(real_cv_sim2real_router)
app.include_router(real_cv_mcp_router)

__all__ = ["app", "real_cv_sim2real_router", "real_cv_mcp_router"]

"""Vercel entrypoint for Fabrient's FastAPI engineering service.

The engineering API is deployed as part of the same repository/deployment as the
Next.js application. Browser requests can therefore use /api/v1/... without a
separate backend URL or CORS configuration.
"""
from engineering.app.main import app

__all__ = ["app"]

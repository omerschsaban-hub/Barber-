"""Integration entrypoint for the complete engineering API surface.

The existing app.main remains the legacy-compatible service entrypoint. This module
provides the complete router composition for deployments that want the final v1
surface without modifying the legacy module in-place.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.main import app as legacy_app
from app.final_pipeline import router as final_router

app = FastAPI(title="Fabrient Engineering API", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[], allow_methods=["GET","POST"], allow_headers=["content-type","authorization"])
for route in legacy_app.routes:
    app.router.routes.append(route)
app.include_router(final_router)

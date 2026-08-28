"""Complete engineering API composition with restrictive CORS defaults."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.cad_routes import router as cad_router
from app.main import app as legacy_app
from app.final_pipeline import router as final_router
from app.manufacturing import router as manufacturing_router
from app.machine_health import router as machine_health_router
from app.sim2real_loop import router as sim2real_router
from app.capabilities import router as capabilities_router

app = FastAPI(title="Fabrient Engineering API", version="1.4.1")
origin = os.getenv("FABRIIENT_WEB_ORIGIN", "http://localhost:3000").strip()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin] if origin else [],
    allow_methods=["GET", "POST"],
    allow_headers=["content-type", "authorization"],
    allow_credentials=True,
)
app.include_router(cad_router)
for route in legacy_app.routes:
    app.router.routes.append(route)
app.include_router(final_router)
app.include_router(manufacturing_router)
app.include_router(machine_health_router)
app.include_router(sim2real_router)
app.include_router(capabilities_router)

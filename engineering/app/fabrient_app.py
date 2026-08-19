"""Complete engineering API composition with restrictive CORS defaults."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.cad_routes import router as cad_router
from app.main import app as legacy_app
from app.final_pipeline import router as final_router
from app.manufacturing import router as manufacturing_router

app = FastAPI(title="Fabrient Engineering API", version="1.3.0")
origin = os.getenv("FABRIENT_WEB_ORIGIN", "http://localhost:3000").strip()
allowed_origins = [origin] if origin else []
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_methods=["GET","POST"], allow_headers=["content-type","authorization"], allow_credentials=True)
app.include_router(cad_router)
for route in legacy_app.routes:
    app.router.routes.append(route)
app.include_router(final_router)
app.include_router(manufacturing_router)

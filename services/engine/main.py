"""Production engineering boundary with evidence-gated quality controls."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engineering.app import env_bootstrap as _env_bootstrap  # noqa: E402,F401
from engineering.app.composed import app  # noqa: E402
from engineering.app.postgres import ensure_schema  # noqa: E402
from engineering.app.owned_auth import _bearer, user_from_token  # noqa: E402
from services.engine.sim2real_policy import auto_fix, TARGET_MAPE_PERCENT  # noqa: E402
from engineering.app.data_flywheel_worker import start_scheduler, run_once  # noqa: E402

# A database is required for production. Bootstrap is idempotent and protected by
# PostgreSQL transactional DDL/advisory locking inside the migration file.
if os.getenv("DATABASE_URL"):
    ensure_schema()
else:
    # Keep health/static CAD validation usable in local development without a DB,
    # but never silently claim that auth/billing/flywheel are production-ready.
    os.environ.setdefault("FLYWHEEL_SCHEDULER_ENABLED", "false")

MAX_JSON_BODY_BYTES = 2 * 1024 * 1024

_flywheel_explicitly_enabled = os.getenv("FLYWHEEL_ENABLE_PRODUCTION", "false").strip().lower() == "true"
if not _flywheel_explicitly_enabled:
    os.environ["FLYWHEEL_SCHEDULER_ENABLED"] = "false"

start_scheduler()

@app.get("/")
def service_root():
    return {
        "status": "ok",
        "service": "fabrient-engineering",
        "message": "Fabrient Engineering API is running.",
        "health": "/health",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }

@app.get("/health")
def health():
    db_ready = bool(os.getenv("DATABASE_URL"))
    return {"status": "ok", "service": "fabrient-engineering", "database_configured": db_ready, "flywheel_enabled": os.getenv("FLYWHEEL_SCHEDULER_ENABLED", "false").lower() == "true"}

@app.get("/v1/health")
def v1_health():
    return health()

@app.get("/internal/data-flywheel/run")
def manual_flywheel_run(token: str | None = None):
    expected = os.getenv("DATA_FLYWHEEL_RUN_TOKEN")
    if not expected or not token or not __import__("hmac").compare_digest(token, expected):
        return JSONResponse(status_code=401, content={"status": "unauthorized"})
    try:
        return {"status": "completed", "result": run_once()}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "failed", "reason": str(exc)[:500]})

PROTECTED_ENGINEERING_ACTIONS = {
    "/v1/dfm/self-fix",
    "/v1/manufacturing/package",
}

@app.middleware("http")
async def engineering_auth_gate(request: Request, call_next):
    if request.method == "POST" and request.url.path in PROTECTED_ENGINEERING_ACTIONS:
        token = _bearer(request, request.headers.get("authorization"))
        try:
            identity = user_from_token(token)
        except Exception:
            return JSONResponse(status_code=503, content={"status": "unavailable", "reason": "Authentication database is unavailable."})
        if not identity:
            return JSONResponse(status_code=401, content={"status": "unauthorized", "reason": "A valid Fabrient session is required for this action."})
        request.state.user = identity
    return await call_next(request)

@app.middleware("http")
async def request_size_gate(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH"}:
        content_type = request.headers.get("content-type", "").lower()
        content_length = request.headers.get("content-length")
        if content_length and "application/json" in content_type:
            try:
                if int(content_length) > MAX_JSON_BODY_BYTES:
                    return JSONResponse(status_code=413, content={
                        "status": "rejected",
                        "reason": "JSON request body is too large.",
                        "max_bytes": MAX_JSON_BODY_BYTES,
                    })
            except ValueError:
                return JSONResponse(status_code=400, content={"status": "rejected", "reason": "Invalid Content-Length."})
    return await call_next(request)

@app.middleware("http")
async def sim2real_quality_gate(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/v1/sim2real/calibrate-and-run":
        try:
            payload = await request.json()
            observations = payload.get("real_observations") or payload.get("observations") or []
            if len(observations) < 10:
                return JSONResponse(status_code=422, content={"status": "blocked", "reason": "At least 10 paired real observations are required; no measurements are invented.", "required": 10, "received": len(observations), "auto_fix": "waiting_for_real_evidence", "accuracy_target_percent": 98.0})
            predicted = [float(x["predicted_mm"]) for x in observations]
            measured = [float(x["measured_mm"]) for x in observations]
            fit, history, target_met = auto_fix(predicted, measured)
            return JSONResponse(content={"status": "validated" if target_met else "blocked", "accuracy_target_percent": 98.0, "max_allowed_mape_percent": TARGET_MAPE_PERCENT, "held_out_mape_percent": fit.mape, "held_out_mae_mm": fit.mae, "correction_scale": fit.scale, "correction_bias_mm": fit.bias, "auto_fix_attempted": True, "auto_fix_history": history, "target_met": target_met, "source": "real_observations_only", "release_claim": "98% sim-to-real target met on deterministic held-out real evidence" if target_met else "blocked: held-out real evidence did not meet the 98% target"})
        except Exception as exc:
            return JSONResponse(status_code=422, content={"status": "blocked", "reason": str(exc)})
    return await call_next(request)

allowed = [origin.strip().rstrip("/") for origin in os.getenv("FABRIENT_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if not allowed and os.getenv("NODE_ENV", "production") == "production":
    allowed = [
        "https://getfabrient.com",
        "https://www.getfabrient.com",
        "https://fabrinat-omega.vercel.app",
        "https://fabrinat-omerschsaban-hubs-projects.vercel.app",
        "https://fabrinat-git-main-omerschsaban-hubs-projects.vercel.app",
    ]

@app.middleware("http")
async def cors_origin_guard(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in allowed:
        return JSONResponse(status_code=403, content={"status": "forbidden", "reason": "Origin is not allowed."})
    response = await call_next(request)
    if origin and origin.rstrip("/") in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin.rstrip("/")
        response.headers["Access-Control-Allow-Credentials"] = "true"
        vary = response.headers.get("Vary", "")
        response.headers["Vary"] = "Origin" if not vary else f"{vary}, Origin"
    return response

if allowed:
    app.add_middleware(CORSMiddleware, allow_origins=allowed, allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "X-Request-ID"], max_age=600)

__all__ = ["app"]

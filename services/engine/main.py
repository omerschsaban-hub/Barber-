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

from engineering.app.composed import app  # noqa: E402
from services.engine.sim2real_policy import auto_fix, TARGET_MAPE_PERCENT  # noqa: E402
from services.engine.data_flywheel_worker import start_scheduler, run_once  # noqa: E402

MAX_JSON_BODY_BYTES = 2 * 1024 * 1024

_flywheel_explicitly_enabled = os.getenv("FLYWHEEL_ENABLE_PRODUCTION", "false").strip().lower() == "true"
if not _flywheel_explicitly_enabled:
    os.environ["FLYWHEEL_SCHEDULER_ENABLED"] = "false"
else:
    _supabase_url = (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_PROJECT_URL") or "").strip()
    _supabase_key = next((os.getenv(name, "").strip() for name in (
        "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY", "SUPABASE_SERVICE_ROLE",
        "SUPABASE_SECRET_KEY", "SUPABASE_KEY",
    ) if os.getenv(name, "").strip()), "")
    if not (_supabase_url and _supabase_key):
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
    return {"status": "ok", "service": "fabrient-engineering"}

@app.get("/v1/health")
def v1_health():
    return health()

@app.get("/internal/data-flywheel/run")
def manual_flywheel_run(token: str | None = None):
    expected = os.getenv("DATA_FLYWHEEL_RUN_TOKEN")
    if not expected or token != expected:
        return JSONResponse(status_code=401, content={"status": "unauthorized"})
    try:
        return {"status": "completed", "result": run_once()}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "failed", "reason": str(exc)[:500]})

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
                return JSONResponse(status_code=422, content={
                    "status": "blocked",
                    "reason": "At least 10 paired real observations are required; no measurements are invented.",
                    "required": 10,
                    "received": len(observations),
                    "auto_fix": "waiting_for_real_evidence",
                    "accuracy_target_percent": 98.0,
                })
            predicted = [float(x["predicted_mm"]) for x in observations]
            measured = [float(x["measured_mm"]) for x in observations]
            fit, history, target_met = auto_fix(predicted, measured)
            return JSONResponse(content={
                "status": "validated" if target_met else "blocked",
                "accuracy_target_percent": 98.0,
                "max_allowed_mape_percent": TARGET_MAPE_PERCENT,
                "held_out_mape_percent": fit.mape,
                "held_out_mae_mm": fit.mae,
                "correction_scale": fit.scale,
                "correction_bias_mm": fit.bias,
                "auto_fix_attempted": True,
                "auto_fix_history": history,
                "target_met": target_met,
                "source": "real_observations_only",
                "release_claim": "98% sim-to-real target met on deterministic held-out real evidence" if target_met else "blocked: held-out real evidence did not meet the 98% target",
            })
        except Exception as exc:
            return JSONResponse(status_code=422, content={"status": "blocked", "reason": str(exc)})
    return await call_next(request)

allowed = [origin.strip().rstrip("/") for origin in os.getenv("FABRIENT_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if not allowed and os.getenv("NODE_ENV", "production") == "production":
    allowed = [
        "https://getfabrient.com",
        "https://www.getfabrient.com",
        "https://fabrinat-omerschsaban-hubs-projects.vercel.app",
        "https://fabrinat-git-main-omerschsaban-hubs-projects.vercel.app",
    ]

@app.middleware("http")
async def cors_origin_guard(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") not in allowed:
        return JSONResponse(status_code=403, content={"status": "forbidden", "reason": "Origin is not allowed."})
    return await call_next(request)

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

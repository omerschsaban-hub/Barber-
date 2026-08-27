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

@app.get("/internal/data-flywheel/run")
def manual_flywheel_run(token: str | None = None):
    expected = os.getenv("DATA_FLYWHEEL_RUN_TOKEN")
    if not expected or not token or not __import__("hmac").compare_digest(token, expected):
        return JSONResponse(status_code=401, content={"status": "unauthorized"})
    try:
        return {"status": "completed", "result": run_once()}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"status": "failed", "reason": str(exc)[:500]})

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

allowed = [origin.strip() for origin in os.getenv("FABRIENT_ALLOWED_ORIGINS", "").split(",") if origin.strip()]
if allowed:
    app.add_middleware(CORSMiddleware, allow_origins=allowed, allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "X-Request-ID"], max_age=600)

__all__ = ["app"]

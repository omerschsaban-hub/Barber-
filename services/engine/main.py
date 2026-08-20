"""Render entrypoint for the Fabrient engineering service.

The production surface includes the composed engineering API. This boundary
also enforces the sim-to-real auto-correction policy so a user never gets a
silent inaccurate calibration: if the measured error is above 1%, Fabrient
attempts a bounded correction and re-evaluates it. If the held-out evidence
still misses 1%, the result is explicitly blocked rather than misreported.
"""
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
from services.engine.sim2real_policy import auto_fix  # noqa: E402


@app.middleware("http")
async def sim2real_quality_gate(request: Request, call_next):
    if request.method == "POST" and request.url.path == "/v1/sim2real/calibrate-and-run":
        try:
            payload = await request.json()
            observations = payload.get("real_observations") or []
            if len(observations) < 10:
                return JSONResponse(status_code=422, content={
                    "status": "blocked",
                    "reason": "At least 10 paired real observations are required; no measurements are invented.",
                    "required": 10,
                    "received": len(observations),
                    "auto_fix": "waiting_for_real_evidence",
                })
            predicted = [float(x["predicted_mm"]) for x in observations]
            measured = [float(x["measured_mm"]) for x in observations]
            fit, history, target_met = auto_fix(predicted, measured)
            return JSONResponse(content={
                "status": "validated" if target_met else "blocked",
                "accuracy_target_percent": 1.0,
                "mape_percent": fit.mape,
                "mae_mm": fit.mae,
                "correction_scale": fit.scale,
                "correction_bias_mm": fit.bias,
                "auto_fix_attempted": True,
                "auto_fix_history": history,
                "target_met": target_met,
                "source": "real_observations_only",
                "message": "Calibration was automatically corrected and rechecked." if target_met else "Automatic correction could not establish <=1% held-out error; workflow is blocked rather than hiding the error.",
            })
        except Exception as exc:
            return JSONResponse(status_code=422, content={"status": "blocked", "reason": str(exc)})
    return await call_next(request)

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

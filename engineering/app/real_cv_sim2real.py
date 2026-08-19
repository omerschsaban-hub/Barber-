from __future__ import annotations

import json
import math
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.metrics import mean_absolute_error

from .openrouter import OpenRouterError, structured_reasoning

router = APIRouter(prefix="/v1", tags=["real-cv-sim2real"])
REAL_CV_VERSION = "real-cv-scale-1.0"
SIM2REAL_VERSION = "physics-ml-sim2real-1.0"
FLEET_VERSION = "bounded-agent-fleet-1.0"


def _line(value: str, name: str) -> np.ndarray:
    try:
        points = np.asarray(json.loads(value), dtype=float)
    except Exception as exc:
        raise HTTPException(422, f"{name} must be JSON [[x,y],[x,y]]") from exc
    if points.shape != (2, 2) or not np.isfinite(points).all():
        raise HTTPException(422, f"{name} must contain two finite [x,y] points")
    return points


def _px(points: np.ndarray) -> float:
    return float(np.linalg.norm(points[1] - points[0]))


class RealObservation(BaseModel):
    predicted_mm: float
    measured_mm: float
    layer_height_mm: float = Field(default=0.2, gt=0)
    print_speed_mm_s: float = Field(default=50, gt=0)
    nozzle_temp_c: float = Field(default=200, gt=0)
    ambient_temp_c: float = 23
    humidity_pct: float = Field(default=50, ge=0, le=100)
    axis: int = Field(default=0, ge=0, le=2)
    machine_id: str | None = None


class Sim2RealRequest(BaseModel):
    nominal_mm: float = Field(gt=0)
    shrinkage_pct: float = Field(ge=0, le=10)
    shrinkage_sigma_pct: float = Field(ge=0, le=5)
    temperature_c: float = Field(gt=0, lt=400)
    temperature_sigma_c: float = Field(ge=0, le=50)
    layer_height_mm: float = Field(default=0.2, gt=0)
    print_speed_mm_s: float = Field(default=50, gt=0)
    nozzle_temp_c: float = Field(default=200, gt=0)
    ambient_temp_c: float = 23
    humidity_pct: float = Field(default=50, ge=0, le=100)
    axis: int = Field(default=0, ge=0, le=2)
    observations: list[RealObservation] = []
    n: int = Field(default=2000, ge=200, le=20000)
    seed: int = 42


class FleetRequest(BaseModel):
    project_id: str
    objective: str
    max_iterations: int = Field(default=5, ge=1, le=20)
    observations: list[RealObservation] = []
    simulation: Sim2RealRequest | None = None
    llm_model: str | None = None


def _features(o: RealObservation, predicted: float | None = None) -> list[float]:
    return [
        o.predicted_mm if predicted is None else predicted,
        o.layer_height_mm, o.print_speed_mm_s, o.nozzle_temp_c,
        o.ambient_temp_c, o.humidity_pct, float(o.axis),
    ]


def _fit(observations: list[RealObservation]) -> dict[str, Any]:
    if len(observations) < 5:
        return {"status": "not_calibrated", "reason": "At least 5 independent real observations are required.", "n_real": len(observations), "model": None}
    X = np.asarray([_features(o) for o in observations], dtype=float)
    y = np.asarray([o.measured_mm - o.predicted_mm for o in observations], dtype=float)
    model = Ridge(alpha=1.0).fit(X, y)
    loo = cross_val_predict(Ridge(alpha=1.0), X, y, cv=LeaveOneOut())
    mae = float(mean_absolute_error(y, loo))
    residual = y - model.predict(X)
    sigma = float(max(np.std(residual, ddof=1), 1e-9))
    return {"status": "validated" if len(observations) >= 10 else "limited", "model": "ridge-residual-v2", "n_real": len(observations), "held_out_mae_mm": mae, "residual_sigma_mm": sigma, "features": ["physics_prediction_mm", "layer_height_mm", "print_speed_mm_s", "nozzle_temp_c", "ambient_temp_c", "humidity_pct", "axis"], "coefficients": model.coef_.tolist(), "intercept_mm": float(model.intercept_), "validation": "leave_one_out", "_model": model}


def _public(value: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if k != "_model"}


@router.post("/cv/measure-real")
async def measure_real_cv(file: UploadFile = File(...), reference_length_mm: float = Form(...), reference_line: str = Form(...), target_line: str = Form(...), reference_uncertainty_mm: float = Form(0.0)):
    if reference_length_mm <= 0 or reference_uncertainty_mm < 0:
        raise HTTPException(422, "reference_length_mm must be positive and reference_uncertainty_mm non-negative")
    raw = await file.read()
    if len(raw) > 10_000_000:
        raise HTTPException(413, "Image exceeds 10 MB")
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise HTTPException(415, "Unsupported image format")
    ref, target = _line(reference_line, "reference_line"), _line(target_line, "target_line")
    ref_px, target_px = _px(ref), _px(target)
    if ref_px < 2 or target_px < 2:
        raise HTTPException(422, "Reference and target lines must be at least 2 pixels long")
    mm_per_px = reference_length_mm / ref_px
    measurement_mm = target_px * mm_per_px
    ref_sigma_px = math.sqrt(0.5**2 + 0.5**2)
    target_sigma_px = ref_sigma_px
    sigma = measurement_mm * math.sqrt((ref_sigma_px / ref_px) ** 2 + (target_sigma_px / target_px) ** 2)
    sigma = math.sqrt(sigma**2 + reference_uncertainty_mm**2)
    return {"status": "measured", "measurement_mm": measurement_mm, "uncertainty_1sigma_mm": sigma, "interval_95_mm": [measurement_mm - 1.96 * sigma, measurement_mm + 1.96 * sigma], "scale": {"reference_length_mm": reference_length_mm, "reference_pixels": ref_px, "mm_per_pixel": mm_per_px}, "image": {"width_px": int(image.shape[1]), "height_px": int(image.shape[0])}, "provenance": {"source": "user_image", "algorithm": "explicit-reference-pixel-scale", "cv_version": REAL_CV_VERSION, "ground_truth_mm": False, "claim_boundary": "Physical reference establishes scale; perspective and lens distortion are not silently corrected."}}


@router.post("/cv/detect-line-candidates")
async def detect_cv_line_candidates(file: UploadFile = File(...)):
    raw = await file.read()
    if len(raw) > 10_000_000:
        raise HTTPException(413, "Image exceeds 10 MB")
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise HTTPException(415, "Unsupported image format")
    edges = cv2.Canny(image, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=max(20, image.shape[1] // 10), maxLineGap=8)
    candidates = []
    if lines is not None:
        for row in lines[:100]:
            p1, p2 = [int(row[0][0]), int(row[0][1])], [int(row[0][2]), int(row[0][3])]
            candidates.append({"p1": p1, "p2": p2, "length_px": float(math.dist(p1, p2))})
    candidates.sort(key=lambda x: x["length_px"], reverse=True)
    return {"status": "candidates", "candidates": candidates[:30], "requires_user_selection": True, "provenance": {"algorithm": "opencv-canny-hough", "cv_version": REAL_CV_VERSION}}


@router.post("/sim2real/run")
def sim2real_run(x: Sim2RealRequest):
    rng = np.random.default_rng(x.seed)
    model_result = _fit(x.observations)
    shrink = rng.normal(x.shrinkage_pct, x.shrinkage_sigma_pct, x.n)
    physics_dims = x.nominal_mm * (1 - shrink / 100.0)
    if model_result.get("_model") is not None:
        model = model_result["_model"]
        Xsim = np.asarray([[float(p), x.layer_height_mm, x.print_speed_mm_s, x.nozzle_temp_c, x.ambient_temp_c, x.humidity_pct, float(x.axis)] for p in physics_dims], dtype=float)
        residual_sigma = float(model_result["residual_sigma_mm"])
        final_dims = physics_dims + model.predict(Xsim) + rng.normal(0.0, residual_sigma, x.n)
        coupling = "learned_from_real_observations"
    else:
        final_dims = physics_dims
        coupling = "not_identified"
    return {"status": "real_calibrated" if model_result.get("status") == "validated" else ("real_informed" if model_result.get("n_real", 0) >= 5 else "physics_only"), "prediction_mm": float(np.mean(final_dims)), "interval_95_mm": [float(np.quantile(final_dims, .025)), float(np.quantile(final_dims, .975))], "n": x.n, "seed": x.seed, "sim_to_real": {"version": SIM2REAL_VERSION, "real_observations": len(x.observations), "residual_coupling": coupling, "model": _public(model_result)}, "domain_randomization": {"parameters": ["shrinkage_pct", "temperature_context", "measurement_residual"], "temperature_effect": "learned only from real observations; never assigned a literature coefficient"}, "samples_summary": {"physics_sigma_mm": float(np.std(physics_dims, ddof=1)), "final_sigma_mm": float(np.std(final_dims, ddof=1)), "min_mm": float(np.min(final_dims)), "max_mm": float(np.max(final_dims))}, "provenance": {"physics": "deterministic_linear_shrinkage", "ml": "ridge_residual_v2" if model_result.get("_model") is not None else None, "real_data_only_for_calibration": True}}


@router.post("/sim2real/compare")
def sim2real_compare(x: Sim2RealRequest):
    result = sim2real_run(x)
    if not x.observations:
        result["comparison"] = {"status": "not_available", "reason": "No real observations supplied."}
        return result
    residuals = np.asarray([o.measured_mm - o.predicted_mm for o in x.observations], dtype=float)
    result["comparison"] = {"status": "available", "n": len(residuals), "mean_residual_mm": float(np.mean(residuals)), "mae_mm": float(np.mean(np.abs(residuals))), "rmse_mm": float(math.sqrt(np.mean(np.square(residuals)))), "observed_sigma_mm": float(np.std(residuals, ddof=1)) if len(residuals) > 1 else None}
    return result


@router.post("/agents/fleet")
async def agent_fleet(x: FleetRequest):
    observations = x.observations or (x.simulation.observations if x.simulation else [])
    model_result = _fit(observations)
    agents = ["evidence", "physics", "cv", "system_identification", "residual_ml", "sim2real", "uncertainty", "experiment", "critic"]
    artifacts: dict[str, Any] = {"evidence": {"real_observations": len(observations), "synthetic_observations_allowed_for_training": False}}
    if x.simulation:
        artifacts["physics"] = {"prediction_mm": x.simulation.nominal_mm * (1 - x.simulation.shrinkage_pct / 100), "sigma_mm": x.simulation.nominal_mm * x.simulation.shrinkage_sigma_pct / 100, "version": "fdm-linear-shrinkage-1.0"}
    else:
        artifacts["physics"] = {"status": "not_run", "reason": "No simulation input supplied."}
    artifacts["cv"] = {"status": "ready", "real_measurement_endpoint": "/v1/cv/measure-real", "scale_rule": "explicit physical reference required"}
    artifacts["system_identification"] = {"status": "ready" if len(observations) >= 8 else "limited", "n_real": len(observations)}
    artifacts["residual_ml"] = _public(model_result)
    artifacts["sim2real"] = sim2real_run(x.simulation) if x.simulation else {"status": "not_run"}
    if artifacts["sim2real"].get("interval_95_mm"):
        lo, hi = artifacts["sim2real"]["interval_95_mm"]
        artifacts["uncertainty"] = {"interval_95_mm": [lo, hi], "width_mm": hi - lo, "status": "bounded"}
    else:
        artifacts["uncertainty"] = {"status": "insufficient_evidence"}
    artifacts["experiment"] = {"status": "proposed" if observations else "insufficient_data", "next_action": "Collect real measurements for the highest-uncertainty feature before claiming validation."}
    blockers = []
    if len(observations) < 5:
        blockers.append("fewer than 5 real observations: residual ML cannot calibrate")
    if x.simulation and model_result.get("status") != "validated":
        blockers.append("sim-to-real model is not validated on >=10 real observations")
    if not observations:
        blockers.append("no real measurements supplied")
    artifacts["critic"] = {"status": "pass" if not blockers else "blocked", "blockers": blockers}
    llm = None
    if x.llm_model:
        try:
            llm_text = await structured_reasoning("You are an engineering orchestration critic. Never invent measurements or engineering values. Summarize only supplied evidence and identify next verification steps.", str({"objective": x.objective, "artifacts": artifacts}), model=x.llm_model)
            llm = {"status": "available", "text": llm_text}
        except OpenRouterError as exc:
            llm = {"status": "unavailable", "reason": str(exc)}
    return {"status": "blocked" if blockers else "complete", "fleet_version": FLEET_VERSION, "project_id": x.project_id, "objective": x.objective, "max_iterations": x.max_iterations, "agents": agents, "completed_agents": agents, "artifacts": artifacts, "llm": llm, "approval_gates": ["physical_execution", "final_acceptance"], "provenance": {"real_measurements": len(observations), "synthetic_data_used_for_ml_training": False, "fleet_is_bounded": True}}

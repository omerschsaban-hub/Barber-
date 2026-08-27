from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import GroupKFold, LeaveOneOut, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .openrouter import OpenRouterError, structured_reasoning
from .owned_auth import _bearer, user_from_token
from .plan_catalog import consume_llm_run

router = APIRouter(prefix="/v1", tags=["real-cv-sim2real"])
REAL_CV_VERSION = "real-cv-scale-2.0"
SIM2REAL_VERSION = "physics-ml-sim2real-2.0"
FLEET_VERSION = "evidence-gated-agent-fleet-2.0"
MIN_CALIBRATION_OBS = 8
MIN_VALIDATED_OBS = 10

class RealObservation(BaseModel):
    predicted_mm: float = Field(gt=0)
    measured_mm: float = Field(gt=0)
    layer_height_mm: float = Field(default=0.2, gt=0)
    print_speed_mm_s: float = Field(default=50, gt=0)
    nozzle_temp_c: float = Field(default=200, gt=0)
    ambient_temp_c: float = 23
    humidity_pct: float = Field(default=50, ge=0, le=100)
    axis: int = Field(default=0, ge=0, le=2)
    machine_id: str | None = None
    feature_id: str | None = None
    observation_id: str | None = None

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
    observations: list[RealObservation] = Field(default_factory=list)
    n: int = Field(default=2000, ge=200, le=20000)
    seed: int = 42

class FleetRequest(BaseModel):
    project_id: str
    objective: str
    max_iterations: int = Field(default=5, ge=1, le=20)
    observations: list[RealObservation] = Field(default_factory=list)
    simulation: Sim2RealRequest | None = None
    llm_model: str | None = None

def _line(value: str, name: str) -> np.ndarray:
    try:
        points = np.asarray(json.loads(value), dtype=float)
    except Exception as exc:
        raise HTTPException(422, f"{name} must be JSON [[x,y],[x,y]]") from exc
    if points.shape != (2, 2) or not np.isfinite(points).all():
        raise HTTPException(422, f"{name} must contain two finite [x,y] points")
    return points

def _quad(value: str | None) -> np.ndarray | None:
    if not value:
        return None
    try:
        points = np.asarray(json.loads(value), dtype=np.float32)
    except Exception as exc:
        raise HTTPException(422, "reference_quad must be JSON [[x,y],[x,y],[x,y],[x,y]]") from exc
    if points.shape != (4, 2) or not np.isfinite(points).all():
        raise HTTPException(422, "reference_quad must contain four finite [x,y] points")
    return points

def _px(points: np.ndarray) -> float:
    return float(np.linalg.norm(points[1] - points[0]))

def _ordered_quad(q: np.ndarray) -> np.ndarray:
    s = q.sum(axis=1)
    d = np.diff(q, axis=1).ravel()
    return np.array([q[np.argmin(s)], q[np.argmin(d)], q[np.argmax(s)], q[np.argmax(d)]], dtype=np.float32)

def _features(o: RealObservation, predicted: float | None = None, temperature: float | None = None) -> list[float]:
    return [o.predicted_mm if predicted is None else predicted, o.layer_height_mm, o.print_speed_mm_s, o.nozzle_temp_c, o.ambient_temp_c if temperature is None else temperature, o.humidity_pct, float(o.axis)]

def _groups(observations: list[RealObservation]) -> np.ndarray:
    return np.asarray([o.machine_id or o.feature_id or o.observation_id or f"row-{i}" for i, o in enumerate(observations)])

def _fit(observations: list[RealObservation]) -> dict[str, Any]:
    n = len(observations)
    if n < MIN_CALIBRATION_OBS:
        return {"status": "not_calibrated", "reason": f"At least {MIN_CALIBRATION_OBS} independent real observations are required.", "n_real": n, "model": None}
    X = np.asarray([_features(o) for o in observations], dtype=float)
    y = np.asarray([o.measured_mm - o.predicted_mm for o in observations], dtype=float)
    groups = _groups(observations)
    model = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(X, y)
    unique_groups = np.unique(groups)
    if len(unique_groups) >= 3:
        cv = GroupKFold(n_splits=min(5, len(unique_groups)))
        held_out = cross_val_predict(make_pipeline(StandardScaler(), Ridge(alpha=1.0)), X, y, cv=cv, groups=groups)
        validation = "group_kfold_by_machine_or_feature"
    else:
        held_out = cross_val_predict(make_pipeline(StandardScaler(), Ridge(alpha=1.0)), X, y, cv=LeaveOneOut())
        validation = "leave_one_out"
    mae = float(mean_absolute_error(y, held_out))
    residual = y - model.predict(X)
    abs_residual = np.abs(y - held_out)
    q95 = float(np.quantile(abs_residual, 0.95, method="higher"))
    sigma = float(max(np.std(residual, ddof=1), 1e-9))
    validated = n >= MIN_VALIDATED_OBS and np.isfinite(q95)
    return {"status": "validated" if validated else "limited", "model": "standardized-ridge-residual-v3", "n_real": n, "n_groups": int(len(unique_groups)), "held_out_mae_mm": mae, "residual_sigma_mm": sigma, "prediction_abs_error_q95_mm": q95, "features": ["physics_prediction_mm", "layer_height_mm", "print_speed_mm_s", "nozzle_temp_c", "ambient_temp_c", "humidity_pct", "axis"], "validation": validation, "training_source": "real_observations_only", "_model": model}

def _public(value: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in value.items() if k != "_model"}

@router.post("/cv/measure-real")
async def measure_real_cv(file: UploadFile = File(...), reference_length_mm: float = Form(...), reference_line: str = Form(...), target_line: str = Form(...), reference_uncertainty_mm: float = Form(0.0), reference_quad: str | None = Form(None)):
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
    quad = _quad(reference_quad)
    rectified = quad is not None
    if quad is not None:
        q = _ordered_quad(quad)
        dst = np.array([[0, 0], [reference_length_mm, 0], [reference_length_mm, reference_length_mm], [0, reference_length_mm]], dtype=np.float32)
        H = cv2.getPerspectiveTransform(q, dst)
        target_rect = cv2.perspectiveTransform(target.reshape(1, -1, 2).astype(np.float32), H)[0]
        measurement_mm = _px(target_rect)
        sigma = math.sqrt((math.sqrt(0.5**2 + 0.5**2))**2 + reference_uncertainty_mm**2)
        scale_method = "explicit-reference-homography"
        mm_per_px = 1.0
    else:
        mm_per_px = reference_length_mm / ref_px
        measurement_mm = target_px * mm_per_px
        px_sigma = math.sqrt(0.5**2 + 0.5**2)
        sigma = math.sqrt((measurement_mm * math.sqrt((px_sigma / ref_px) ** 2 + (px_sigma / target_px) ** 2)) ** 2 + reference_uncertainty_mm**2)
        scale_method = "explicit-reference-pixel-scale"
    return {"status": "measured", "measurement_mm": measurement_mm, "uncertainty_1sigma_mm": sigma, "interval_95_mm": [measurement_mm - 1.96 * sigma, measurement_mm + 1.96 * sigma], "scale": {"reference_length_mm": reference_length_mm, "reference_pixels": ref_px, "mm_per_pixel": mm_per_px, "perspective_corrected": rectified}, "image": {"width_px": int(image.shape[1]), "height_px": int(image.shape[0]), "sha256": hashlib.sha256(raw).hexdigest()}, "provenance": {"source": "user_image", "algorithm": scale_method, "cv_version": REAL_CV_VERSION, "ground_truth_mm": False, "claim_boundary": "Physical reference establishes scale; CV measurement is evidence, not final physical acceptance."}}

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
        for row in lines[:200]:
            p1, p2 = [int(row[0][0]), int(row[0][1])], [int(row[0][2]), int(row[0][3])]
            candidates.append({"p1": p1, "p2": p2, "length_px": float(math.dist(p1, p2))})
    candidates.sort(key=lambda x: x["length_px"], reverse=True)
    return {"status": "candidates", "candidates": candidates[:50], "requires_user_selection": True, "provenance": {"algorithm": "opencv-canny-hough", "cv_version": REAL_CV_VERSION}}

@router.post("/sim2real/run")
def sim2real_run(x: Sim2RealRequest):
    rng = np.random.default_rng(x.seed)
    model_result = _fit(x.observations)
    shrink = rng.normal(x.shrinkage_pct, x.shrinkage_sigma_pct, x.n)
    temp = rng.normal(x.temperature_c, x.temperature_sigma_c, x.n)
    physics_dims = x.nominal_mm * (1 - shrink / 100.0)
    if model_result.get("_model") is not None:
        model = model_result["_model"]
        Xsim = np.asarray([[float(p), x.layer_height_mm, x.print_speed_mm_s, x.nozzle_temp_c, float(t), x.humidity_pct, float(x.axis)] for p, t in zip(physics_dims, temp)], dtype=float)
        final_dims = physics_dims + model.predict(Xsim)
        bound = float(model_result["prediction_abs_error_q95_mm"])
        coupling = "validated_real_residual_model" if model_result["status"] == "validated" else "real_informed_unvalidated"
    else:
        final_dims = physics_dims
        bound = float(np.std(physics_dims, ddof=1) * 1.96)
        coupling = "physics_only"
    return {"status": "real_calibrated" if model_result.get("status") == "validated" else ("real_informed" if model_result.get("n_real", 0) >= MIN_CALIBRATION_OBS else "physics_only"), "prediction_mm": float(np.mean(final_dims)), "interval_95_mm": [float(np.mean(final_dims) - bound), float(np.mean(final_dims) + bound)], "n": x.n, "seed": x.seed, "sim_to_real": {"version": SIM2REAL_VERSION, "real_observations": len(x.observations), "residual_coupling": coupling, "model": _public(model_result)}, "domain_randomization": {"parameters": ["shrinkage_pct", "temperature_c", "measurement_residual"], "temperature_sampling": {"mean_c": x.temperature_c, "sigma_c": x.temperature_sigma_c}, "temperature_effect": "Only learned from real observations; no literature coefficient is substituted."}, "samples_summary": {"physics_sigma_mm": float(np.std(physics_dims, ddof=1)), "final_sigma_mm": float(np.std(final_dims, ddof=1)), "min_mm": float(np.min(final_dims)), "max_mm": float(np.max(final_dims))}, "provenance": {"physics": "deterministic_linear_shrinkage", "ml": "standardized_ridge_residual_v3" if model_result.get("_model") is not None else None, "real_data_only_for_calibration": True}}

@router.post("/sim2real/compare")
def sim2real_compare(x: Sim2RealRequest):
    result = sim2real_run(x)
    if not x.observations:
        result["comparison"] = {"status": "not_available", "reason": "No real observations supplied."}
        return result
    residuals = np.asarray([o.measured_mm - o.predicted_mm for o in x.observations], dtype=float)
    result["comparison"] = {"status": "available", "n": len(residuals), "mean_residual_mm": float(np.mean(residuals)), "mae_mm": float(np.mean(np.abs(residuals))), "rmse_mm": float(math.sqrt(np.mean(np.square(residuals)))), "observed_sigma_mm": float(np.std(residuals, ddof=1)) if len(residuals) > 1 else None}
    return result

@router.post("/sim2real/calibrate-and-run")
def calibrate_and_run(x: Sim2RealRequest):
    if len(x.observations) < MIN_VALIDATED_OBS:
        return {"status": "blocked", "reason": f"Need at least {MIN_VALIDATED_OBS} real observations before a calibrated sim-to-real claim.", "real_observations": len(x.observations), "next_action": "Measure independent physical features across the relevant machine/process domain."}
    result = sim2real_run(x)
    if result["status"] != "real_calibrated":
        return {"status": "blocked", "result": result, "reason": "Real observations exist but validation gates did not pass."}
    return {"status": "validated", "result": result, "release_claim": "calibrated prediction with empirical held-out error bound; not physical acceptance"}

@router.post("/agents/fleet")
async def agent_fleet(request: Request, x: FleetRequest):
    observations = x.observations or (x.simulation.observations if x.simulation else [])
    model_result = _fit(observations)
    agents = ["evidence", "physics", "cv", "system_identification", "residual_ml", "sim2real", "uncertainty", "experiment", "critic"]
    artifacts: dict[str, Any] = {
        "evidence": {"real_observations": len(observations), "synthetic_observations_allowed_for_training": False, "unique_machines": len({o.machine_id for o in observations if o.machine_id}), "unique_features": len({o.feature_id for o in observations if o.feature_id})},
        "physics": ({"prediction_mm": x.simulation.nominal_mm * (1 - x.simulation.shrinkage_pct / 100), "sigma_mm": x.simulation.nominal_mm * x.simulation.shrinkage_sigma_pct / 100, "version": "fdm-linear-shrinkage-2.0"} if x.simulation else {"status": "not_run", "reason": "No simulation input supplied."}),
        "cv": {"status": "ready", "real_measurement_endpoint": "/v1/cv/measure-real", "line_candidates_endpoint": "/v1/cv/detect-line-candidates", "physical_reference_required": True},
        "system_identification": {"status": "ready" if len(observations) >= MIN_CALIBRATION_OBS else "limited", "n_real": len(observations)},
        "residual_ml": _public(model_result),
        "sim2real": sim2real_run(x.simulation) if x.simulation else {"status": "not_run"},
    }
    if artifacts["sim2real"].get("interval_95_mm"):
        lo, hi = artifacts["sim2real"]["interval_95_mm"]
        artifacts["uncertainty"] = {"interval_95_mm": [lo, hi], "width_mm": hi - lo, "status": "bounded_empirically"}
    else:
        artifacts["uncertainty"] = {"status": "insufficient_evidence"}
    blockers = []
    if len(observations) < MIN_CALIBRATION_OBS:
        blockers.append(f"fewer than {MIN_CALIBRATION_OBS} real observations: residual ML cannot calibrate")
    if x.simulation and model_result.get("status") != "validated":
        blockers.append(f"sim-to-real model is not validated on >= {MIN_VALIDATED_OBS} real observations")
    if not observations:
        blockers.append("no real measurements supplied")
    artifacts["experiment"] = {"status": "proposed" if observations else "insufficient_data", "next_action": "Collect real measurements for the highest-uncertainty machine/feature group before claiming validation."}
    artifacts["critic"] = {"status": "pass" if not blockers else "blocked", "blockers": blockers}
    llm = None
    plan_usage = None
    if x.llm_model:
        identity = user_from_token(_bearer(request, request.headers.get('authorization')))
        if not identity:
            raise HTTPException(status_code=401, detail='Sign in is required for an LLM run')
        plan_usage = consume_llm_run(identity['user_id'])
        if not plan_usage['allowed']:
            raise HTTPException(status_code=429, detail={'message': 'Monthly AI run limit reached', **plan_usage})
        try:
            llm_text = await structured_reasoning("You are an engineering orchestration critic. Never invent measurements, coefficients, tolerances, or physical test results. Summarize only supplied evidence and identify next verification steps.", str({"objective": x.objective, "artifacts": artifacts}), model=x.llm_model)
            llm = {"status": "available", "text": llm_text}
        except OpenRouterError as exc:
            llm = {"status": "unavailable", "reason": str(exc)}
    return {"status": "blocked" if blockers else "complete", "fleet_version": FLEET_VERSION, "project_id": x.project_id, "objective": x.objective, "max_iterations": x.max_iterations, "agents": agents, "completed_agents": agents, "artifacts": artifacts, "llm": llm, "plan_usage": plan_usage, "approval_gates": ["physical_execution", "final_acceptance"], "provenance": {"real_measurements": len(observations), "synthetic_data_used_for_ml_training": False, "fleet_is_evidence_gated": True}}

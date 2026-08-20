from __future__ import annotations

import base64
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .cad_kernel import extract_step
from .manufacturing import DFMRequest, analyze, self_fix
from .real_cv_sim2real import RealObservation, Sim2RealRequest, sim2real_run

router = APIRouter(prefix="/v1/sim2real", tags=["sim2real-loop"])


class FeatureEvidence(BaseModel):
    feature_id: str
    nominal_mm: float | None = None
    measured_mm: float | None = None
    lower_tol_mm: float | None = None
    upper_tol_mm: float | None = None
    kind: str = "dimension"


class LoopRequest(BaseModel):
    project_id: str = "fabrient-sim2real"
    revision: str = "unversioned"
    material: str = "unknown"
    machine: str = "unknown"
    step_b64: str
    step_filename: str = "model.step"
    measurements: dict[str, float] = Field(default_factory=dict)
    features: list[FeatureEvidence] = Field(default_factory=list)
    simulation: dict[str, Any] = Field(default_factory=dict)
    observations: list[RealObservation] = Field(default_factory=list)
    seed: int = 42
    human_release_approved: bool = False


def _decode_step(value: str) -> bytes:
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise HTTPException(422, "step_b64 is not valid base64") from exc
    if not raw:
        raise HTTPException(422, "STEP payload is empty")
    if len(raw) > 25_000_000:
        raise HTTPException(413, "STEP payload exceeds 25 MB")
    return raw


def _feature_checks(features: list[FeatureEvidence]) -> list[dict[str, Any]]:
    out = []
    for f in features:
        status = "indeterminate"
        reason = "No measured value supplied."
        if f.measured_mm is not None and f.nominal_mm is not None:
            lo = f.nominal_mm + (f.lower_tol_mm or 0.0)
            hi = f.nominal_mm + (f.upper_tol_mm or 0.0)
            status = "pass" if lo <= f.measured_mm <= hi else "fail"
            reason = "Measured value is inside declared bounds." if status == "pass" else "Measured value is outside declared bounds."
        out.append({"feature_id": f.feature_id, "kind": f.kind, "nominal_mm": f.nominal_mm, "measured_mm": f.measured_mm, "lower_tol_mm": f.lower_tol_mm, "upper_tol_mm": f.upper_tol_mm, "status": status, "reason": reason})
    return out


def _experiment_plan(observations: list[RealObservation]) -> dict[str, Any]:
    if not observations:
        return {"status": "needs_measurement", "next_test": "Measure an independent critical feature on the target machine/process.", "selection_basis": "No real observations yet."}
    residuals = sorted(((abs(o.measured_mm - o.predicted_mm), o) for o in observations), key=lambda x: x[0], reverse=True)
    worst = residuals[0][1]
    return {"status": "ready_for_next_test", "next_test": {"feature_id": worst.feature_id or "highest-residual-feature", "machine_id": worst.machine_id or "unspecified", "predicted_mm": worst.predicted_mm, "measured_mm": worst.measured_mm, "absolute_residual_mm": abs(worst.measured_mm - worst.predicted_mm)}, "selection_basis": "Highest observed prediction residual; execution remains human-gated."}


def _release_gates(cad: dict[str, Any], dfm: dict[str, Any], sim: dict[str, Any], features: list[dict[str, Any]], observations: list[RealObservation], approved: bool) -> list[dict[str, Any]]:
    calibrated = sim.get("status") == "real_calibrated"
    measured_features = sum(1 for f in features if f.get("status") in {"pass", "fail"})
    return [
        {"gate": "step_binding", "status": "pass" if cad.get("status") == "validated" else "fail"},
        {"gate": "dfm", "status": "pass" if int(dfm.get("blocker_count", 0)) == 0 else "fail", "blockers": int(dfm.get("blocker_count", 0))},
        {"gate": "physical_evidence", "status": "pass" if len(observations) >= 10 else "blocked", "real_observations": len(observations), "required": 10},
        {"gate": "calibration_validation", "status": "pass" if calibrated else "blocked", "reason": "Held-out real-observation validation is required for a calibrated sim-to-real claim."},
        {"gate": "feature_measurements", "status": "pass" if measured_features else "blocked", "measured_features": measured_features},
        {"gate": "human_release", "status": "approved" if approved else "required"},
    ]


@router.post("/loop")
def run_full_loop(x: LoopRequest):
    raw = _decode_step(x.step_b64)
    step_hash = hashlib.sha256(raw).hexdigest()
    with tempfile.TemporaryDirectory(prefix="fabrient-loop-") as d:
        path = Path(d) / Path(x.step_filename).name
        path.write_bytes(raw)
        cad = extract_step(str(path))
    if cad.get("status") != "validated":
        raise HTTPException(422, cad.get("reason", "STEP extraction failed"))

    dfm_req = DFMRequest(part_name=x.project_id, revision=x.revision, material=x.material, machine=x.machine, measurements=x.measurements)
    before = analyze(dfm_req)
    fixed = self_fix(dfm_req)
    after = fixed.get("after", before)

    sim_input = dict(x.simulation)
    sim_input.setdefault("nominal_mm", float(x.measurements.get("nominal_mm", 10.0)))
    sim_input.setdefault("shrinkage_pct", float(x.measurements.get("shrinkage_pct", 0.8)))
    sim_input.setdefault("shrinkage_sigma_pct", float(x.measurements.get("shrinkage_sigma_pct", 0.1)))
    sim_input.setdefault("temperature_c", float(x.measurements.get("temperature_c", 220.0)))
    sim_input.setdefault("temperature_sigma_c", float(x.measurements.get("temperature_sigma_c", 2.0)))
    sim_input["seed"] = x.seed
    sim_input["observations"] = x.observations
    sim = sim2real_run(Sim2RealRequest(**sim_input))

    feature_results = _feature_checks(x.features)
    experiment = _experiment_plan(x.observations)
    gates = _release_gates(cad, after, sim, feature_results, x.observations, x.human_release_approved)
    release_ready = all(g["status"] in {"pass", "approved"} for g in gates)

    provenance = {
        "project_id": x.project_id,
        "step_sha256": step_hash,
        "synthetic": False,
        "stages": ["CAD", "DFM", "FIX", "VERIFY", "SIMULATE", "PHYSICAL_TEST", "MEASURE", "COMPARE", "CALIBRATE", "NEXT_EXPERIMENT", "RELEASE"],
        "evidence_policy": "real observations are required for calibration; no fabricated measurements or confidence",
    }
    return {
        "status": "release_candidate" if release_ready else "evidence_loop_open",
        "release_ready": release_ready,
        "cad": cad,
        "dfm": {"before": before, "fix": fixed, "after": after},
        "feature_inspector": feature_results,
        "simulation": sim,
        "physical_test": {"observation_count": len(x.observations), "planner": experiment},
        "prediction_vs_reality": sim.get("comparison", {"status": "not_available"}),
        "calibration": sim.get("sim_to_real", {}).get("model", {"status": "not_calibrated"}),
        "release_gates": gates,
        "provenance": provenance,
    }


@router.post("/next-experiment")
def next_experiment(observations: list[RealObservation]):
    return _experiment_plan(observations)

from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .real_cv_sim2real import RealObservation, Sim2RealRequest, sim2real_compare, sim2real_run

router = APIRouter(prefix="/v1/sim2real", tags=["sim2real"])


class Experiment(BaseModel):
    name: str
    predicted_mm: float = Field(gt=0)
    measured_mm: float = Field(gt=0)
    cost_minutes: float = Field(default=10, gt=0)
    machine_id: str | None = None
    feature_id: str | None = None


class RealityLoopRequest(BaseModel):
    nominal_mm: float = Field(gt=0)
    shrinkage_pct: float = Field(ge=0, le=10)
    shrinkage_sigma_pct: float = Field(ge=0, le=5)
    temperature_c: float = Field(gt=0, lt=400)
    temperature_sigma_c: float = Field(ge=0, le=50)
    observations: list[RealObservation] = Field(default_factory=list)
    candidate_experiments: list[Experiment] = Field(default_factory=list)
    target_mae_mm: float = Field(default=0.1, gt=0)
    max_iterations: int = Field(default=5, ge=1, le=20)
    seed: int = 42


def _next_experiment(observations: list[RealObservation], candidates: list[Experiment]) -> dict[str, Any]:
    if not candidates:
        return {
            "status": "needs_experiment",
            "reason": "No executable physical experiment was supplied. The software will not invent one or pretend hardware was operated.",
        }
    if not observations:
        return {"status": "selected", "selected": candidates[0].model_dump(), "selection_basis": "No real evidence yet; choose the lowest-cost valid baseline experiment."}

    residual = np.asarray([o.measured_mm - o.predicted_mm for o in observations], dtype=float)
    spread = float(np.std(residual)) if len(residual) > 1 else abs(float(residual[0]))
    ranked = []
    for e in candidates:
        # Simple, deterministic information-per-cost heuristic. It deliberately does
        # not claim causal certainty; later experiments can replace this with a
        # domain-specific Bayesian/Fisher-information planner.
        predicted_residual = abs(e.measured_mm - e.predicted_mm)
        information = predicted_residual + spread + 1e-9
        ranked.append((information / e.cost_minutes, e))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return {
        "status": "selected",
        "selected": ranked[0][1].model_dump(),
        "selection_basis": "highest deterministic residual-information-per-minute score",
        "score": ranked[0][0],
    }


def _trust(result: dict[str, Any], observations: list[RealObservation], target: float) -> dict[str, Any]:
    model = result.get("sim_to_real", {}).get("model", {})
    mae = model.get("held_out_mae_mm")
    if mae is None:
        return {"status": "insufficient_evidence", "reason": "Held-out error cannot be established without enough independent real observations."}
    return {
        "status": "validated" if float(mae) <= target and len(observations) >= 10 else "not_validated",
        "held_out_mae_mm": float(mae),
        "target_mae_mm": target,
        "real_observations": len(observations),
        "boundary": "Validated only for the conditions represented by the real observations; this is not a universal accuracy claim.",
    }


@router.post("/loop")
def run_reality_loop(x: RealityLoopRequest):
    sim = Sim2RealRequest(
        nominal_mm=x.nominal_mm,
        shrinkage_pct=x.shrinkage_pct,
        shrinkage_sigma_pct=x.shrinkage_sigma_pct,
        temperature_c=x.temperature_c,
        temperature_sigma_c=x.temperature_sigma_c,
        observations=x.observations,
        seed=x.seed,
    )
    result = sim2real_run(sim)
    comparison = sim2real_compare(sim).get("comparison", {"status": "not_available"})
    next_test = _next_experiment(x.observations, x.candidate_experiments)
    trust = _trust(result, x.observations, x.target_mae_mm)

    return {
        "status": "validated" if trust["status"] == "validated" else "loop_open",
        "objective": "reduce simulation-to-reality error with the fewest informative physical experiments",
        "simulation": result,
        "comparison": comparison,
        "calibration": result.get("sim_to_real", {}).get("model", {}),
        "next_experiment": next_test,
        "trust_envelope": trust,
        "automation": {
            "software_loop": ["compare", "identify", "calibrate", "residual_ml", "validate", "select_next_experiment"],
            "physical_execution": "not automated in MVP; requires real measurements supplied by the connected test workflow",
            "fabrication_policy": "never fabricate physical observations, validation, or hardware execution",
        },
        "iteration": {"current_observations": len(x.observations), "max_iterations": x.max_iterations},
    }


@router.post("/next-experiment")
def next_experiment(observations: list[RealObservation], candidates: list[Experiment] = []):
    return _next_experiment(observations, candidates)

from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["mcp-compatibility"])


def reviewable(operation: str, payload: dict[str, Any] | None = None, *, human_gate: bool = False) -> dict[str, Any]:
    payload = payload or {}
    return {
        "status": "reviewable",
        "operation": operation,
        "inputs_received": sorted(payload.keys()),
        "next_step": "Supply the operation-specific evidence; Fabrient refuses to invent missing measurements or process coefficients.",
        "human_gate": human_gate,
        "provenance": {"source": "mcp_compatibility_boundary", "synthetic": False},
    }


@router.post("/v1/toolbox/release_manufacturing_package")
def release_package(payload: dict[str, Any]):
    # This compatibility path must return the same authoritative package contract as manufacturing.py.
    from .manufacturing import PackageRequest, manufacturing_package
    inner = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
    package = manufacturing_package(PackageRequest(**inner))
    eligible = package["release_status"] == "release_candidate"
    return {
        "operation": "release_manufacturing_package",
        "eligible": eligible,
        "package": package,
        "human_release_required": True,
    }


@router.post("/v1/toolbox/check_data_quality")
def check_data_quality(payload: dict[str, Any]):
    rows = payload.get("observations") or payload.get("rows") or []
    missing = 0
    non_finite = 0
    for row in rows:
        if not isinstance(row, dict):
            missing += 1
            continue
        for value in row.values():
            if isinstance(value, float) and not math.isfinite(value):
                non_finite += 1
    return {"status": "pass" if rows and not missing and not non_finite else "review_required", "row_count": len(rows), "missing_or_invalid_rows": missing, "non_finite_values": non_finite, "provenance": {"source": "deterministic_data_quality", "synthetic": False}}


@router.post("/v1/toolbox/audit_training_data")
def audit_training_data(payload: dict[str, Any]):
    rows = payload.get("observations") or payload.get("rows") or []
    real_only = all(isinstance(r, dict) and r.get("synthetic") is not True for r in rows)
    return {"status": "eligible_for_review" if rows and real_only else "blocked", "row_count": len(rows), "real_observations_only": real_only, "synthetic_rows_rejected": not real_only, "provenance": {"source": "training_data_audit", "synthetic": False}}


@router.post("/v1/toolbox/cad_fit_review")
def cad_fit_review(payload: dict[str, Any]):
    return reviewable("cad_fit_review", payload)


@router.post("/v1/toolbox/physics_interval")
def physics_interval(payload: dict[str, Any]):
    if {"prediction_mm", "sigma_mm"}.issubset(payload):
        sigma = float(payload["sigma_mm"])
        if sigma < 0:
            raise HTTPException(422, "sigma_mm must be non-negative")
        mu = float(payload["prediction_mm"])
        return {"status": "computed", "interval_95_mm": [mu - 1.96 * sigma, mu + 1.96 * sigma], "provenance": {"source": "deterministic_physics_interval", "synthetic": False}}
    return reviewable("physics_interval", payload)


@router.post("/v1/toolbox/physics_provenance")
def physics_provenance(payload: dict[str, Any]):
    return {"status": "available", "source": "deterministic_physics", "physics_version": "fdm-linear-shrinkage-1.0", "algorithm_version": "deterministic-sim2real-1.0", "assumptions": {"temperature_used_as_context_only": True, "no_literature_value_substituted": True}, "inputs_received": sorted(payload.keys())}


@router.post("/v1/toolbox/simulation_domain_randomization")
def simulation_domain_randomization(payload: dict[str, Any]):
    return reviewable("simulation_domain_randomization", payload)


@router.post("/v1/toolbox/ml_residual_fit")
def ml_residual_fit(payload: dict[str, Any]):
    rows = payload.get("observations") or payload.get("residuals") or []
    return {"status": "limited" if len(rows) < 12 else "ready_for_validation", "n": len(rows), "reason": "Residual ML requires real observations and held-out validation.", "provenance": {"source": "real_observations_only", "synthetic": False}}


@router.post("/v1/toolbox/ml_residual_validation")
def ml_residual_validation(payload: dict[str, Any]):
    rows = payload.get("observations") or []
    return {"status": "limited" if len(rows) < 12 else "validation_required", "n": len(rows), "method": "held_out_validation", "provenance": {"source": "real_observations_only", "synthetic": False}}


@router.post("/v1/toolbox/ml_prediction_uncertainty")
def ml_prediction_uncertainty(payload: dict[str, Any]):
    return reviewable("ml_prediction_uncertainty", payload)


@router.post("/v1/toolbox/deterministic_reverification")
def deterministic_reverification(payload: dict[str, Any]):
    return reviewable("deterministic_reverification", payload)


@router.post("/v1/toolbox/deterministic_next_experiment")
def deterministic_next_experiment(payload: dict[str, Any]):
    return reviewable("deterministic_next_experiment", payload, human_gate=True)


@router.post("/v1/toolbox/agent_step")
def agent_step(payload: dict[str, Any]):
    return {"status": "approval_required", "action": "none", "iterations": 0, "reason": "Engineering actions remain human-approved in v1.", "inputs_received": sorted(payload.keys())}


@router.post("/v1/toolbox/risk_estimate")
def risk_estimate(payload: dict[str, Any]):
    return reviewable("risk_estimate", payload)


@router.post("/v1/toolbox/final_system_identification")
def final_system_identification(payload: dict[str, Any]):
    return reviewable("final_system_identification", payload)


@router.post("/v1/toolbox/engineering_agent_run")
def engineering_agent_run(payload: dict[str, Any]):
    return {"status": "approval_required", "action": "none", "reason": "Bounded engineering actions remain human-approved in v1.", "provenance": {"source": "mcp_compatibility_boundary", "synthetic": False}}


@router.post("/v1/toolbox/run_bounded_engineering_review")
def bounded_engineering_review(payload: dict[str, Any]):
    return {"status": "reviewable", "operation": "run_bounded_engineering_review", "blocked_actions": ["physical_execution", "automatic_release", "fabricated_measurements"], "inputs_received": sorted(payload.keys()), "human_gate": True}


# Direct lifecycle aliases used by the authoritative MCP registry.
@router.post("/v1/agent/step")
def agent_step_alias(payload: dict[str, Any]):
    return {"status": "approval_required", "action": "none", "iterations": 0, "reason": "Engineering actions remain human-approved in v1.", "inputs_received": sorted(payload.keys())}

@router.post("/v1/final/risk")
def final_risk_alias(payload: dict[str, Any]):
    from .final_pipeline import RiskRequest, computed_risk
    return computed_risk(RiskRequest(**payload))

@router.post("/v1/final/system-identification")
def final_system_identification_alias(payload: dict[str, Any]):
    return reviewable("final_system_identification", payload)

@router.post("/v1/final/import/confirm")
def inspection_confirm_alias(payload: dict[str, Any]):
    return {"status": "reviewable", "operation": "inspection_confirm", "inputs_received": sorted(payload.keys()), "next_step": "Confirm only against the previewed real inspection data.", "human_gate": True, "provenance": {"source": "inspection_confirmation_boundary", "synthetic": False}}

# Generic compatibility boundary for every authoritative toolbox endpoint.

@router.post("/v1/toolbox/{operation}")
def generic_toolbox_operation(operation: str, payload: dict[str, Any]):
    return reviewable(operation, payload, human_gate=True)

from __future__ import annotations

"""Shared deterministic operation implementations for the engineering API.

The MCP surface has many named capabilities, but they must not be fake aliases that
always return ``blocked``.  This module gives each capability a bounded, honest
implementation.  It never invents geometry or physical measurements: operations
requiring evidence return a structured ``blocked`` result explaining exactly what
is missing, while operations that can be evaluated from supplied numeric evidence
actually compute the result.
"""

from dataclasses import asdict, dataclass
from math import sqrt
from statistics import mean
from typing import Any, Iterable


def _num(payload: dict[str, Any], *names: str) -> float | None:
    for name in names:
        if name in payload and payload[name] is not None:
            try:
                value = float(payload[name])
            except (TypeError, ValueError):
                return None
            if value == value and abs(value) != float("inf"):
                return value
            return None
    return None


def _observations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    value = payload.get("observations", payload.get("real_observations", []))
    return value if isinstance(value, list) else []


def _blocked(operation: str, reason: str, **extra: Any) -> dict[str, Any]:
    return {"operation": operation, "status": "blocked", "engineering_claims": False, "reason": reason, **extra}


def _pass(operation: str, **extra: Any) -> dict[str, Any]:
    return {"operation": operation, "status": "pass", "engineering_claims": True, **extra}


def _comparison(operation: str, value: float | None, limit: float | None, *, lower: bool = True) -> dict[str, Any]:
    if value is None or limit is None:
        return _blocked(operation, "required numeric evidence is missing", required_inputs=["measured_value", "limit"])
    passed = value >= limit if lower else value <= limit
    return {"operation": operation, "status": "pass" if passed else "fail", "engineering_claims": True,
            "measured": value, "limit": limit, "margin": (value - limit) if lower else (limit - value),
            "evidence": "caller-supplied measurement"}


def _linear_fit(x: list[list[float]], y: list[float], ridge: float = 1e-6) -> list[float]:
    """Small ridge regression using only the Python standard library."""
    if not x or len(x) != len(y):
        raise ValueError("x and y must have equal non-zero lengths")
    p = len(x[0])
    if p == 0 or any(len(row) != p for row in x):
        raise ValueError("feature rows must have equal non-zero width")
    a = [[0.0] * p for _ in range(p)]
    b = [0.0] * p
    for row, target in zip(x, y):
        for i in range(p):
            b[i] += row[i] * target
            for j in range(p):
                a[i][j] += row[i] * row[j]
    for i in range(p):
        a[i][i] += ridge
    for i in range(p):
        pivot = max(range(i, p), key=lambda r: abs(a[r][i]))
        if abs(a[pivot][i]) < 1e-12:
            raise ValueError("singular feature matrix")
        a[i], a[pivot] = a[pivot], a[i]
        for r in range(i + 1, p):
            q = a[r][i] / a[i][i]
            for c in range(i, p):
                a[r][c] -= q * a[i][c]
            b[r] -= q * b[i]
    w = [0.0] * p
    for i in range(p - 1, -1, -1):
        w[i] = (b[i] - sum(a[i][j] * w[j] for j in range(i + 1, p))) / a[i][i]
    return w


def _model_operation(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    obs = _observations(payload)
    if len(obs) < 10:
        return _blocked(operation, "at least 10 real observations are required for held-out validation", observations=len(obs), required_observations=10, source="real_observations_only")
    rows: list[list[float]] = []
    targets: list[float] = []
    for item in obs:
        if not isinstance(item, dict):
            continue
        features = item.get("features", item.get("x"))
        target = item.get("target", item.get("y", item.get("residual_mm")))
        if isinstance(features, list) and target is not None:
            try:
                rows.append([float(v) for v in features])
                targets.append(float(target))
            except (TypeError, ValueError):
                continue
        elif "predicted_mm" in item and "measured_mm" in item:
            try:
                predicted = float(item["predicted_mm"])
                measured = float(item["measured_mm"])
            except (TypeError, ValueError):
                continue
            rows.append([1.0, predicted])
            targets.append(measured - predicted)
    if len(rows) < 10:
        return _blocked(operation, "observations must contain numeric features/targets or predicted_mm/measured_mm pairs", usable_observations=len(rows))
    width = len(rows[0])
    cut = max(5, int(len(rows) * 0.8))
    if len(rows) - cut < 10:
        return _blocked(operation, "at least 10 held-out observations are required", usable_observations=len(rows), holdout=len(rows) - cut)
    try:
        weights = _linear_fit(rows[:cut], targets[:cut])
    except ValueError as exc:
        return _blocked(operation, f"model fit failed: {exc}")
    errors = [sum(a * b for a, b in zip(weights, row)) - target for row, target in zip(rows[cut:], targets[cut:])]
    mae = mean(abs(e) for e in errors)
    rmse = sqrt(mean(e * e for e in errors))
    sigma = sqrt(mean((e - mean(errors)) ** 2 for e in errors)) if len(errors) > 1 else 0.0
    validated = mae <= float(payload.get("max_mae_mm", 0.25))
    return {"operation": operation, "status": "validated" if validated else "blocked", "engineering_claims": validated,
            "observations": len(rows), "train_observations": cut, "holdout_observations": len(errors),
            "mae_mm": mae, "rmse_mm": rmse, "sigma_mm": sigma, "weights": weights,
            "model_version": "residual-linear-v2", "source": "real_observations_only",
            "validation": {"held_out": True, "max_mae_mm": float(payload.get("max_mae_mm", 0.25)), "passed": validated}}


def _inspection(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    checks = []
    mappings = {
        "wall": ("wall_thickness_mm", "minimum_wall_thickness_mm", True),
        "clearance": ("clearance_mm", "minimum_clearance_mm", True),
        "hole": ("hole_diameter_mm", "minimum_hole_diameter_mm", True),
        "overhang": ("overhang_angle_deg", "maximum_overhang_angle_deg", False),
        "bridge": ("bridge_length_mm", "maximum_bridge_length_mm", False),
    }
    for key, (value_key, limit_key, lower) in mappings.items():
        if value_key in payload or limit_key in payload:
            result = _comparison(key, _num(payload, value_key), _num(payload, limit_key), lower=lower)
            checks.append(result)
    if "measured_mm" in payload and "tolerance_mm" in payload:
        measured = _num(payload, "measured_mm")
        tolerance = _num(payload, "tolerance_mm")
        nominal = _num(payload, "nominal_mm", "target_mm")
        if measured is not None and tolerance is not None and nominal is not None:
            deviation = abs(measured - nominal)
            checks.append({"operation": "dimension", "status": "pass" if deviation <= tolerance else "fail", "deviation_mm": deviation, "tolerance_mm": tolerance})
    if not checks:
        return _blocked(operation, "no measurable inspection inputs were supplied", required_inputs=["wall_thickness_mm/minimum_wall_thickness_mm", "clearance_mm/minimum_clearance_mm", "or equivalent evidence"])
    failed = [c for c in checks if c.get("status") == "fail"]
    return {"operation": operation, "status": "fail" if failed else "pass", "engineering_claims": True,
            "checks": checks, "failed_checks": len(failed), "passed_checks": len(checks) - len(failed), "evidence": "caller-supplied measurements"}


def _risk(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    findings = payload.get("findings", [])
    if not isinstance(findings, list):
        return _blocked(operation, "findings must be an array")
    ranked = []
    for i, item in enumerate(findings):
        if not isinstance(item, dict):
            continue
        score = _num(item, "risk_score", "score")
        if score is None:
            score = 0.0
        score = max(0.0, min(1.0, score))
        level = "critical" if score >= .8 else "high" if score >= .6 else "medium" if score >= .35 else "low"
        ranked.append({"id": str(item.get("id", f"finding-{i + 1}")), "category": str(item.get("category", "engineering")),
                       "message": str(item.get("message", "No description supplied")), "risk_score": score, "level": level,
                       "source": str(item.get("source", "supplied evidence"))})
    ranked.sort(key=lambda x: (-x["risk_score"], x["id"]))
    return {"operation": operation, "status": "pass", "engineering_claims": True, "risk_map": ranked,
            "summary": {level: sum(x["level"] == level for x in ranked) for level in ("critical", "high", "medium", "low")}}


def _experiment(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("experiments", payload.get("candidates", []))
    if not isinstance(candidates, list) or not candidates:
        return _blocked(operation, "candidate experiments are required", required_inputs=["experiments"])
    ranked = []
    for i, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            continue
        uncertainty = _num(candidate, "uncertainty", "uncertainty_mm") or 0.0
        cost = max(_num(candidate, "cost", "cost_score") or 1.0, 1e-9)
        information = _num(candidate, "information_gain", "expected_information_gain") or 0.0
        score = information * (1.0 + uncertainty) / cost
        ranked.append({"id": str(candidate.get("id", i + 1)), "score": score, "information_gain": information,
                       "uncertainty": uncertainty, "cost": cost})
    ranked.sort(key=lambda x: (-x["score"], x["id"]))
    return {"operation": operation, "status": "pass", "engineering_claims": False, "ranking": ranked,
            "selection": ranked[0] if ranked else None, "method": "information-gain per normalized cost"}


def _release(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    gates = payload.get("gates", {})
    if not isinstance(gates, dict):
        return _blocked(operation, "gates must be an object")
    required = ("geometry_verified", "dfm_passed", "inspection_plan_ready", "provenance_complete", "physical_acceptance")
    missing = [name for name in required if gates.get(name) is not True]
    return {"operation": operation, "status": "ready_for_human_release" if not missing else "blocked",
            "released": False, "engineering_claims": False, "missing_gates": missing,
            "human_release_required": True, "release_policy": "no automatic consequential release"}


def run_tool_operation(operation: str, payload: dict[str, Any], *, topology_verified: bool = False) -> dict[str, Any]:
    """Execute one named MCP/toolbox capability without pretending unsupported evidence exists."""
    p = dict(payload or {})
    if operation in {"check_wall_thickness", "check_clearances", "check_holes", "check_overhangs", "check_bridges", "check_tolerances", "check_fit",
                     "validate_dimension", "cad_wall_clearance_review", "cad_hole_review", "cad_overhang_review", "cad_bridge_review", "cad_tolerance_review"}:
        if operation == "validate_dimension":
            nominal = _num(p, "nominal_mm"); measured = _num(p, "measured_mm"); tolerance = _num(p, "tolerance_mm")
            if nominal is None or measured is None or tolerance is None or tolerance < 0:
                return _blocked(operation, "nominal_mm, measured_mm and non-negative tolerance_mm are required")
            deviation = measured - nominal
            return {"operation": operation, "status": "pass" if abs(deviation) <= tolerance else "fail", "engineering_claims": True,
                    "nominal_mm": nominal, "measured_mm": measured, "deviation_mm": deviation, "tolerance_mm": tolerance}
        aliases = {"cad_wall_clearance_review": "check_wall_thickness", "cad_hole_review": "check_holes", "cad_overhang_review": "check_overhangs", "cad_bridge_review": "check_bridges", "cad_tolerance_review": "check_tolerances"}
        return _inspection(operation, {**p, "_alias": aliases.get(operation, operation)})
    if operation in {"inspect_part", "analyze_geometry", "extract_features", "analyze_dfm", "find_manufacturing_risks", "score_manufacturability", "cad_manufacturing_risk"}:
        if not topology_verified and not p.get("geometry_verified"):
            return _blocked(operation, "verified CAD topology is required; upload STEP/STP or provide verified geometry evidence")
        inspection = _inspection(operation, p)
        return {**inspection, "topology_verified": True, "geometry_source": "CadQuery/OCCT"}
    if operation in {"risk_map"}:
        return _risk(operation, p)
    if operation in {"estimate_risk", "risk_estimate", "ml_data_quality", "check_data_quality"}:
        obs = _observations(p)
        if not obs:
            return _blocked(operation, "observations are required for data-quality analysis")
        missing = sum(1 for row in obs if not isinstance(row, dict) or any(v is None for v in row.values()))
        return {"operation": operation, "status": "pass" if missing == 0 else "fail", "engineering_claims": True,
                "observations": len(obs), "rows_with_missing_values": missing, "completeness": 1 - missing / len(obs),
                "duplicate_rows": len(obs) - len({repr(sorted(x.items())) for x in obs if isinstance(x, dict)})}
    if operation in {"fit_residual_model", "validate_residual_model", "calibrate_model_uncertainty", "run_model_diagnostics", "estimate_prediction_interval",
                     "detect_distribution_shift", "ml_machine_system_id", "system_identification", "final_system_identification", "residual_uncertainty",
                     "calibrate_from_observations", "calibration_fit"} or operation.startswith("ml_"):
        return _model_operation(operation, p)
    if operation in {"rank_experiments", "compare_experiments", "propose_next_experiment", "next_experiment", "select_next_experiment"}:
        return _experiment(operation, p)
    if operation in {"generate_manufacturing_package", "manufacturing_package", "manufacturing_release_candidate", "validate_manufacturing_package",
                     "release_manufacturing_package", "manufacturing_release_gate"}:
        return _release(operation, p)
    if operation in {"auto_fix_dfm", "dfm_self_fix", "manufacturing_dfm_fix_verify"}:
        # Geometry mutation is intentionally gated. We can verify a supplied post-fix result,
        # but never fabricate a modified CAD file.
        if p.get("post_fix_verified") is True:
            return {"operation": operation, "status": "pass", "engineering_claims": True, "modified": True,
                    "post_fix_verified": True, "provenance": p.get("provenance", {})}
        return _blocked(operation, "a bounded CAD mutation and independent post-fix kernel verification are required", required_inputs=["proposed_change", "post_fix_verified"])
    if operation in {"trace_provenance", "verify_release_provenance", "manufacturing_provenance"}:
        provenance = p.get("provenance")
        if not isinstance(provenance, dict) or not provenance:
            return _blocked(operation, "provenance record is required")
        return {"operation": operation, "status": "pass", "engineering_claims": False, "provenance": provenance, "complete": all(bool(v) for v in provenance.values())}
    if operation in {"validate_material", "identify_machine", "identify_process", "validate_machine_envelope"}:
        required = "material" if operation == "validate_material" else "machine" if operation == "identify_machine" else "process" if operation == "identify_process" else "machine_envelope"
        value = p.get(required)
        return {"operation": operation, "status": "pass" if value else "blocked", "engineering_claims": bool(value), "value": value, "required_input": required}
    if operation in {"build_inspection_plan", "manufacturing_inspection_plan"}:
        critical = p.get("critical_dimensions", p.get("dimensions", []))
        if not isinstance(critical, list) or not critical:
            return _blocked(operation, "critical dimensions are required")
        return {"operation": operation, "status": "pass", "engineering_claims": False,
                "plan": [{"dimension": d, "method": "calibrated measurement", "repeatability": "recorded", "acceptance": "nominal/tolerance"} for d in critical]}
    if operation in {"generate_physical_build_guide", "physical_build_guide"}:
        return {"operation": operation, "status": "pass", "engineering_claims": False,
                "steps": ["lock revision and provenance", "manufacture controlled sample", "measure critical dimensions", "perform physical fit test", "record evidence", "review release gates"]}
    if operation in {"get_next_best_action", "run_bounded_engineering_review", "engineering_agent_run", "agent_step", "agent_graph", "agent_fleet_run", "llm_engineering_critic", "run_engineering_agent"}:
        return {"operation": operation, "status": "pass", "engineering_claims": False,
                "next_action": "collect the missing evidence for the highest-risk unresolved gate",
                "evidence_required": ["verified geometry", "deterministic checks", "physical evidence where applicable"],
                "llm_role": "planning and interpretation only; it cannot override engineering verification"}
    if operation in {"approve_experiment", "refuse_experiment", "record_experiment", "record_activity", "write_audit_record", "save_project_state"}:
        if not p:
            return _blocked(operation, "record payload is required")
        return {"operation": operation, "status": "recorded", "engineering_claims": False, "record": p}
    if operation in {"get_project_state", "get_project_history", "get_audit_trail", "get_review_share", "create_review_share"}:
        return {"operation": operation, "status": "pass", "engineering_claims": False, "data": p}
    if operation in {"run_domain_randomization", "run_sensitivity_analysis", "simulation_run", "sim2real_run", "run_calibrated_sim2real", "compare_sim_to_real"}:
        return {"operation": operation, "status": "pass" if p.get("simulation_evidence") else "blocked", "engineering_claims": bool(p.get("simulation_evidence")),
                "reason": None if p.get("simulation_evidence") else "simulation parameters/results are required; no simulated result is fabricated"}
    if operation in {"acceptance_gate", "deterministic_acceptance"}:
        gates = p.get("gates", {})
        if not isinstance(gates, dict):
            return _blocked(operation, "gates object is required")
        failed = [k for k, v in gates.items() if v is not True]
        return {"operation": operation, "status": "pass" if not failed else "fail", "accepted": not failed,
                "engineering_claims": True, "failed_gates": failed, "gates": gates}
    if operation in {"release_manufacturing_package", "manufacturing_release_gate"}:
        return _release(operation, p)
    # Unknown registered operations must remain explicit rather than silently succeeding.
    return _blocked(operation, "registered capability has no safe implementation mapping yet", implementation_status="not_implemented")

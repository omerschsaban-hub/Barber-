from __future__ import annotations

import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

from mcp_capabilities import TOOLBOX_CAPABILITIES, DIRECT_CAPABILITIES

ENGINEERING_API = os.getenv("FABRIENT_ENGINEERING_API", "http://localhost:8000").rstrip("/")
MCP_AUTH_TOKEN = os.getenv("FABRIENT_MCP_AUTH_TOKEN", "").strip()

mcp = FastMCP("Fabrient Engineering")

async def _request(method: str, path: str, *, payload: dict[str, Any] | None = None, timeout: float = 120.0) -> Any:
    if not path.startswith("/") or path.startswith("//") or not path.startswith("/v1/"):
        raise ValueError("Only Fabrient /v1 API paths are permitted")
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"} if MCP_AUTH_TOKEN else {}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.request(method.upper(), f"{ENGINEERING_API}{path}", json=payload or {}, headers=headers)
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
        if r.status_code >= 400:
            raise RuntimeError(f"Engineering API {r.status_code}: {data}")
        return data

# Canonical Fabrient capability registry. Every capability is a first-class
# MCP tool so clients can discover and call the complete engineering surface.
CAPABILITIES: dict[str, tuple[str, str]] = {
    "predict_dimension": ("/v1/predict", "Deterministic dimension prediction with provenance and uncertainty."),
    "simulate_dimension": ("/v1/simulate", "Run bounded domain-randomized dimension simulation."),
    "calibrate_from_measurements": ("/v1/calibrate", "Fit residual calibration using real observations and held-out validation."),
    "calculate_uncertainty": ("/v1/uncertainty", "Combine physics, measurement, and model uncertainty."),
    "run_acceptance_gate": ("/v1/acceptance", "Run the deterministic acceptance/refusal gate."),
    "calculate_reverification": ("/v1/reverification", "Calculate a bounded re-verification interval from observed drift and wear."),
    "select_next_experiment": ("/v1/next-experiment", "Select the highest-information real experiment."),
    "preview_inspection_import": ("/v1/import/preview", "Preview and map a messy inspection CSV before ingestion."),
    "extract_step_geometry": ("/v1/geometry/step", "Extract supported geometry information from STEP/STP."),
    "measure_from_image": ("/v1/cv/measure", "Run computer-vision measurement on an uploaded image."),
    "inspect_part": ("/v1/toolbox/inspect_part", "Inspect a part and return structured engineering findings."),
    "analyze_geometry": ("/v1/toolbox/analyze_geometry", "Analyze geometry features and engineering risks."),
    "extract_features": ("/v1/toolbox/extract_features", "Extract manufacturability and geometry features."),
    "calculate_bounding_box": ("/v1/toolbox/calculate_bounding_box", "Calculate and report the geometry bounding box."),
    "analyze_tolerances": ("/v1/toolbox/analyze_tolerances", "Analyze tolerance requirements and risk."),
    "analyze_clearances": ("/v1/toolbox/analyze_clearances", "Analyze fit and clearance risks."),
    "analyze_wall_thickness": ("/v1/toolbox/analyze_wall_thickness", "Analyze minimum wall and manufacturability risk."),
    "analyze_overhangs": ("/v1/toolbox/analyze_overhangs", "Analyze overhang and support risk."),
    "analyze_bridges": ("/v1/toolbox/analyze_bridges", "Analyze bridge-length manufacturing risk."),
    "analyze_holes": ("/v1/toolbox/analyze_holes", "Analyze holes and feature manufacturability."),
    "analyze_threads": ("/v1/toolbox/analyze_threads", "Analyze threaded-feature manufacturability."),
    "analyze_dfm": ("/v1/toolbox/analyze_dfm", "Run deterministic DFM analysis."),
    "auto_fix_dfm": ("/v1/toolbox/auto_fix_dfm", "Apply only allowed deterministic DFM fixes."),
    "verify_fixes": ("/v1/toolbox/verify_fixes", "Re-run verification after engineering fixes."),
    "score_manufacturability": ("/v1/toolbox/score_manufacturability", "Score manufacturability using engineering checks."),
    "find_manufacturing_risks": ("/v1/toolbox/find_manufacturing_risks", "Identify manufacturing risks and evidence."),
    "suggest_orientation": ("/v1/toolbox/suggest_orientation", "Suggest bounded manufacturing orientation options."),
    "analyze_support_strategy": ("/v1/toolbox/analyze_support_strategy", "Analyze support strategy for FDM manufacturing."),
    "analyze_shrinkage_risk": ("/v1/toolbox/analyze_shrinkage_risk", "Analyze shrinkage-driven dimensional risk."),
    "analyze_warp_risk": ("/v1/toolbox/analyze_warp_risk", "Analyze thermal warping risk."),
    "identify_machine": ("/v1/toolbox/identify_machine", "Identify the machine/process context for an engineering operation."),
    "identify_process": ("/v1/toolbox/identify_process", "Identify manufacturing process parameters."),
    "system_identification": ("/v1/system-identification", "Estimate machine/process behavior from real measurements."),
    "analyze_machine_drift": ("/v1/toolbox/analyze_machine_drift", "Analyze production drift for a machine."),
    "analyze_service_wear": ("/v1/toolbox/analyze_service_wear", "Analyze service wear from observed history."),
    "compare_machines": ("/v1/toolbox/compare_machines", "Compare measured machine/process behavior."),
    "compare_revisions": ("/v1/toolbox/compare_revisions", "Compare engineering revisions and measured outcomes."),
    "fit_residual_model": ("/v1/toolbox/fit_residual_model", "Fit a residual model only from permitted real observations."),
    "validate_residual_model": ("/v1/toolbox/validate_residual_model", "Run held-out validation for a residual model."),
    "calibrate_model_uncertainty": ("/v1/toolbox/calibrate_model_uncertainty", "Calibrate residual-model uncertainty."),
    "run_model_diagnostics": ("/v1/toolbox/run_model_diagnostics", "Inspect residual-model diagnostics and failure modes."),
    "estimate_prediction_interval": ("/v1/toolbox/estimate_prediction_interval", "Estimate a bounded prediction interval."),
    "detect_distribution_shift": ("/v1/toolbox/detect_distribution_shift", "Detect production distribution shift from evidence."),
    "check_data_quality": ("/v1/toolbox/check_data_quality", "Check measurement and inspection data quality."),
    "audit_training_data": ("/v1/toolbox/audit_training_data", "Audit provenance and eligibility of model-training observations."),
    "run_domain_randomization": ("/v1/toolbox/run_domain_randomization", "Run bounded simulation/domain randomization."),
    "run_sensitivity_analysis": ("/v1/toolbox/run_sensitivity_analysis", "Quantify sensitivity to engineering parameters."),
    "rank_experiments": ("/v1/toolbox/rank_experiments", "Rank candidate physical experiments by information value."),
    "compare_experiments": ("/v1/toolbox/compare_experiments", "Compare measured experiment outcomes."),
    "record_experiment": ("/v1/toolbox/record_experiment", "Record a real physical experiment and provenance."),
    "approve_experiment": ("/v1/toolbox/approve_experiment", "Record human approval before physical execution."),
    "refuse_experiment": ("/v1/toolbox/refuse_experiment", "Record why a physical experiment is refused."),
    "generate_manufacturing_package": ("/v1/toolbox/generate_manufacturing_package", "Generate the verified manufacturing package."),
    "generate_physical_build_guide": ("/v1/toolbox/generate_physical_build_guide", "Generate the physical build guide."),
    "validate_manufacturing_package": ("/v1/manufacturing/package", "Generate and validate the manufacturing package gates."),
    "release_manufacturing_package": ("/v1/toolbox/release_manufacturing_package", "Release only after required gates pass."),
    "generate_inspection_record": ("/v1/inspection-report/csv", "Generate the structured inspection record as CSV."),
    "export_inspection_csv": ("/v1/inspection-report/csv", "Export inspection data as CSV."),
    "generate_report_pdf": ("/v1/inspection-report/pdf", "Generate the engineering report PDF."),
    "verify_release_provenance": ("/v1/toolbox/trace_provenance", "Verify provenance and release evidence."),
    "get_project_state": ("/v1/toolbox/get_project_state", "Retrieve persistent engineering state."),
    "save_project_state": ("/v1/toolbox/save_project_state", "Persist engineering state."),
    "get_next_best_action": ("/v1/toolbox/get_next_best_action", "Return the next engineering action."),
    "record_activity": ("/v1/toolbox/record_activity", "Record an engineering lifecycle activity."),
    "get_project_history": ("/v1/toolbox/get_project_history", "Retrieve project engineering history."),
    "create_review_share": ("/v1/toolbox/create_review_share", "Create a shareable engineering review context."),
    "get_review_share": ("/v1/toolbox/get_review_share", "Retrieve a shared engineering review context."),
    "write_audit_record": ("/v1/toolbox/write_audit_record", "Write an engineering provenance/audit record."),
    "get_audit_trail": ("/v1/toolbox/get_audit_trail", "Retrieve engineering provenance and audit history."),
    "run_engineering_agent": ("/v1/agents/run", "Run bounded engineering-agent orchestration."),
}

# Add every existing manufacturing capability as a first-class MCP tool.
# The MCP remains an adapter layer; the engineering service remains the source
# of truth for deterministic algorithms, ML validation, and release gates.
for _name, _description in TOOLBOX_CAPABILITIES.items():
    CAPABILITIES.setdefault(_name, (f"/v1/toolbox/{_name}", _description))

# Direct API mappings supersede older toolbox aliases.
for _name, (_path, _description) in DIRECT_CAPABILITIES.items():
    CAPABILITIES[_name] = (_path, _description)

async def _call_capability(name: str, path: str, payload: dict[str, Any]) -> Any:
    return await _request("POST", path, payload=payload)


def _register(name: str, path: str, description: str) -> None:
    async def tool(payload: dict[str, Any] | None = None) -> Any:
        return await _call_capability(name, path, payload or {})
    tool.__name__ = name
    tool.__doc__ = description
    mcp.tool(name=name, description=description)(tool)

for _name, (_path, _description) in CAPABILITIES.items():
    _register(_name, _path, _description)

@mcp.tool(name="list_fabrient_capabilities", description="Return the complete callable Fabrient MCP capability registry and endpoint mappings.")
async def list_fabrient_capabilities() -> dict[str, Any]:
    return {"count": len(CAPABILITIES), "capabilities": [{"name": n, "path": p, "description": d} for n, (p, d) in sorted(CAPABILITIES.items())]}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

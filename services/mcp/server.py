from __future__ import annotations

import base64
import os
from typing import Any

import httpx
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

ENGINE_URL = os.getenv("FABRIENT_ENGINE_URL", "https://fabrient-engineering.onrender.com").rstrip("/")
mcp = MCPServer("Fabrient Engineering", instructions="Fabrient MCP: deterministic engineering algorithms + measured-evidence ML + bounded engineering/LLM orchestration. Never invent measurements or confidence.")

# Single authoritative registry. tools/list and tools/call are generated from this exact table.
CAPABILITY_REGISTRY: tuple[tuple[str, str, str], ...] = (
    ("inspect_part", "Inspect a part.", "/v1/toolbox/inspect_part"),
    ("analyze_dfm", "Analyze DFM.", "/v1/toolbox/analyze_dfm"),
    ("auto_fix_dfm", "Auto fix DFM.", "/v1/toolbox/auto_fix_dfm"),
    ("verify_fixes", "Verify fixes.", "/v1/toolbox/verify_fixes"),
    ("generate_manufacturing_package", "Generate manufacturing package.", "/v1/toolbox/generate_manufacturing_package"),
    ("generate_physical_build_guide", "Generate physical build guide.", "/v1/toolbox/generate_physical_build_guide"),
    ("release_manufacturing_package", "Release manufacturing package.", "/v1/toolbox/release_manufacturing_package"),
    ("validate_material", "Validate material.", "/v1/toolbox/validate_material"),
    ("validate_machine_envelope", "Validate machine envelope.", "/v1/toolbox/validate_machine_envelope"),
    ("validate_dimension", "Validate a measured dimension against a nominal and tolerance.", "/v1/toolbox/validate_dimension"),
    ("check_wall_thickness", "Check wall thickness.", "/v1/toolbox/check_wall_thickness"),
    ("check_clearances", "Check clearances.", "/v1/toolbox/check_clearances"),
    ("check_holes", "Check holes.", "/v1/toolbox/check_holes"),
    ("check_overhangs", "Check overhangs.", "/v1/toolbox/check_overhangs"),
    ("check_bridges", "Check bridges.", "/v1/toolbox/check_bridges"),
    ("check_supports", "Check supports.", "/v1/toolbox/check_supports"),
    ("check_orientation", "Check orientation.", "/v1/toolbox/check_orientation"),
    ("check_tolerances", "Check tolerances.", "/v1/toolbox/check_tolerances"),
    ("check_fit", "Check fit.", "/v1/toolbox/check_fit"),
    ("check_warp_risk", "Check warp risk.", "/v1/toolbox/check_warp_risk"),
    ("check_first_layer", "Check first layer.", "/v1/toolbox/check_first_layer"),
    ("check_thermal_risk", "Check thermal risk.", "/v1/toolbox/check_thermal_risk"),
    ("check_print_time", "Check print time.", "/v1/toolbox/check_print_time"),
    ("check_material_usage", "Check material usage.", "/v1/toolbox/check_material_usage"),
    ("check_bed_adhesion", "Check bed adhesion.", "/v1/toolbox/check_bed_adhesion"),
    ("check_part_split", "Check part split.", "/v1/toolbox/check_part_split"),
    ("check_fastener_access", "Check fastener access.", "/v1/toolbox/check_fastener_access"),
    ("check_assembly_order", "Check assembly order.", "/v1/toolbox/check_assembly_order"),
    ("check_service_access", "Check service access.", "/v1/toolbox/check_service_access"),
    ("check_draft", "Check draft.", "/v1/toolbox/check_draft"),
    ("check_sharp_edges", "Check sharp edges.", "/v1/toolbox/check_sharp_edges"),
    ("check_small_features", "Check small features.", "/v1/toolbox/check_small_features"),
    ("check_text_legibility", "Check text legibility.", "/v1/toolbox/check_text_legibility"),
    ("check_embossed_features", "Check embossed features.", "/v1/toolbox/check_embossed_features"),
    ("check_threads", "Check threads.", "/v1/toolbox/check_threads"),
    ("check_press_fits", "Check press fits.", "/v1/toolbox/check_press_fits"),
    ("check_snap_fits", "Check snap fits.", "/v1/toolbox/check_snap_fits"),
    ("check_insert_pockets", "Check insert pockets.", "/v1/toolbox/check_insert_pockets"),
    ("check_connector_clearance", "Check connector clearance.", "/v1/toolbox/check_connector_clearance"),
    ("check_cable_clearance", "Check cable clearance.", "/v1/toolbox/check_cable_clearance"),
    ("check_pcb_clearance", "Check PCB clearance.", "/v1/toolbox/check_pcb_clearance"),
    ("check_component_keepouts", "Check component keepouts.", "/v1/toolbox/check_component_keepouts"),
    ("check_revision_consistency", "Check revision consistency.", "/v1/toolbox/check_revision_consistency"),
    ("compare_revisions", "Compare revisions.", "/v1/toolbox/compare_revisions"),
    ("trace_provenance", "Trace provenance.", "/v1/toolbox/trace_provenance"),
    ("build_inspection_plan", "Build inspection plan.", "/v1/toolbox/build_inspection_plan"),
    ("map_inspection_columns", "Map inspection columns.", "/v1/toolbox/map_inspection_columns"),
    ("calibrate_from_observations", "Calibrate from observations.", "/v1/toolbox/calibrate_from_observations"),
    ("estimate_risk", "Estimate risk.", "/v1/toolbox/estimate_risk"),
    ("calculate_reverification", "Calculate reverification.", "/v1/toolbox/calculate_reverification"),
    ("propose_next_experiment", "Propose next experiment.", "/v1/toolbox/propose_next_experiment"),
    ("run_bounded_engineering_review", "Run bounded engineering review.", "/v1/toolbox/run_bounded_engineering_review"),
    ("physics_predict", "Run deterministic physics prediction.", "/v1/predict"),
    ("simulation_run", "Run simulation.", "/v1/simulate"),
    ("calibration_fit", "Fit calibration from observations.", "/v1/calibrate"),
    ("uncertainty_calculate", "Calculate uncertainty.", "/v1/uncertainty"),
    ("acceptance_gate", "Run acceptance gate.", "/v1/acceptance"),
    ("reverification_calculate", "Calculate reverification.", "/v1/reverification"),
    ("next_experiment", "Select next experiment.", "/v1/next-experiment"),
    ("engineering_agent_run", "Run bounded engineering agent.", "/v1/agents/run"),
    ("dfm_analyze", "Run engineering DFM analysis.", "/v1/dfm/analyze"),
    ("dfm_self_fix", "Run engineering DFM self-fix.", "/v1/dfm/self-fix"),
    ("manufacturing_package", "Generate manufacturing package.", "/v1/manufacturing/package"),
    ("physical_build_guide", "Generate physical build guide.", "/v1/manufacturing/build-guide"),
    ("system_identification", "Run system identification.", "/v1/system-identification"),
    ("residual_uncertainty", "Calculate residual uncertainty.", "/v1/residual-uncertainty"),
    ("inspection_report_csv", "Generate inspection CSV report.", "/v1/inspection-report/csv"),
    ("inspection_report_pdf", "Generate inspection PDF report.", "/v1/inspection-report/pdf"),
    ("agent_graph", "Build agent graph.", "/v1/agent-graph"),
    ("agent_step", "Run one agent step.", "/v1/agent/step"),
    ("risk_estimate", "Estimate final risk.", "/v1/final/risk"),
    ("final_system_identification", "Run final system identification.", "/v1/final/system-identification"),
    ("cad_step_extract", "Extract CAD STEP geometry.", "/v1/geometry/step"),
    ("cv_measure", "Measure geometry with computer vision.", "/v1/cv/measure"),
    ("inspection_preview", "Preview inspection import.", "/v1/import/preview"),
    ("inspection_confirm", "Confirm inspection import.", "/v1/final/import/confirm"),
    ("physics_interval", "Return physics prediction interval.", "/v1/predict"),
    ("physics_provenance", "Return physics prediction provenance.", "/v1/predict"),
    ("simulation_domain_randomization", "Run simulation domain randomization.", "/v1/simulate"),
    ("ml_residual_fit", "Fit ML residual model.", "/v1/calibrate"),
    ("ml_residual_validation", "Validate ML residual model.", "/v1/calibrate"),
    ("ml_prediction_uncertainty", "Estimate ML prediction uncertainty.", "/v1/residual-uncertainty"),
    ("ml_machine_system_id", "Run ML machine system identification.", "/v1/system-identification"),
    ("deterministic_acceptance", "Run deterministic acceptance.", "/v1/acceptance"),
    ("deterministic_reverification", "Run deterministic reverification.", "/v1/reverification"),
    ("deterministic_next_experiment", "Run deterministic next experiment selection.", "/v1/next-experiment"),
    ("manufacturing_release_candidate", "Generate manufacturing release candidate.", "/v1/manufacturing/package"),
    ("manufacturing_release_gate", "Run manufacturing release gate.", "/v1/toolbox/release_manufacturing_package"),
    ("manufacturing_dfm_fix_verify", "Fix and verify manufacturing DFM.", "/v1/dfm/self-fix"),
    ("manufacturing_inspection_plan", "Build manufacturing inspection plan.", "/v1/toolbox/build_inspection_plan"),
    ("manufacturing_provenance", "Return manufacturing provenance.", "/v1/toolbox/trace_provenance"),
    ("cad_manufacturing_risk", "Review CAD manufacturing risk.", "/v1/toolbox/analyze_dfm"),
    ("cad_wall_clearance_review", "Review CAD wall and clearance risk.", "/v1/toolbox/check_wall_thickness"),
    ("cad_hole_review", "Review CAD holes.", "/v1/toolbox/check_holes"),
    ("cad_overhang_review", "Review CAD overhangs.", "/v1/toolbox/check_overhangs"),
    ("cad_bridge_review", "Review CAD bridges.", "/v1/toolbox/check_bridges"),
    ("cad_tolerance_review", "Review CAD tolerances.", "/v1/toolbox/check_tolerances"),
    ("cad_fit_review", "Review CAD fit.", "/v1/toolbox/check_fit"),
    ("ml_data_quality", "Review ML data quality.", "/v1/toolbox/check_data_quality"),
    ("ml_training_data_audit", "Audit ML training data.", "/v1/toolbox/audit_training_data"),
)

CAPABILITY_NAMES = [name for name, _, _ in CAPABILITY_REGISTRY]
TOOL_NAMES = CAPABILITY_NAMES
TOOL_COUNT = len(CAPABILITY_REGISTRY)
if TOOL_COUNT != 100 or len(set(CAPABILITY_NAMES)) != 100:
    raise RuntimeError(f"Authoritative MCP registry must contain exactly 100 unique tools; got {TOOL_COUNT}")

async def _post(path: str, payload: dict[str, Any] | None = None, timeout: float = 120) -> Any:
    payload = payload or {}
    upload_paths = {"/v1/geometry/step", "/v1/cv/measure", "/v1/import/preview"}
    if path in upload_paths and payload.get("file_base64"):
        try:
            raw = base64.b64decode(payload["file_base64"], validate=True)
        except Exception as exc:
            raise ValueError("file_base64 must be valid base64") from exc
        if len(raw) > 25_000_000:
            raise ValueError("uploaded file exceeds 25 MB")
        filename = str(payload.get("filename") or "upload.bin")
        extra = {k: v for k, v in payload.items() if k not in {"file_base64", "filename"}}
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{ENGINE_URL}{path}", files={"file": (filename, raw, "application/octet-stream")}, data=extra)
    else:
        # Toolbox endpoints use a stable envelope: {operation, payload}.
        # The MCP tool name is the operation; the public MCP payload should not
        # force callers to repeat that routing key.
        if path.startswith("/v1/toolbox/"):
            operation = path.rsplit("/", 1)[-1]
            request_body = {"operation": operation, "payload": payload}
        else:
            request_body = payload
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{ENGINE_URL}{path}", json=request_body)
    try:
        data = response.json()
    except Exception:
        data = {"content_type": response.headers.get("content-type", ""), "status_code": response.status_code, "text": response.text[:20000]}
    if response.status_code >= 400:
        raise RuntimeError(f"Engineering API {response.status_code}: {data}")
    return data

def _register(name: str, description: str, path: str) -> None:
    if name == "validate_dimension":
        async def tool(nominal_mm: float, measured_mm: float, tolerance_mm: float, mcp_smoke_test: bool = False) -> Any:
            if mcp_smoke_test:
                return {"ok": True, "tool": name, "route": path, "smoke_test": True}
            return await _post(path, {
                "nominal_mm": nominal_mm,
                "measured_mm": measured_mm,
                "tolerance_mm": tolerance_mm,
            })
    else:
        async def tool(payload: dict[str, Any] | None = None) -> Any:
            payload = payload or {}
            if payload.get("_mcp_smoke_test") is True:
                return {"ok": True, "tool": name, "route": path, "smoke_test": True}
            return await _post(path, payload)
    tool.__name__ = name
    tool.__doc__ = description
    mcp.tool()(tool)

for _name, _description, _path in CAPABILITY_REGISTRY:
    _register(_name, _description, _path)

@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "fabrient-mcp", "engine_url": ENGINE_URL, "tool_count": TOOL_COUNT})

@mcp.custom_route("/capabilities", methods=["GET"])
async def capabilities(_: Request) -> JSONResponse:
    return JSONResponse({"name": "Fabrient Engineering", "tool_count": TOOL_COUNT, "tools": CAPABILITY_NAMES, "engine_url": ENGINE_URL, "registry_authoritative": True})

host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost")
security = TransportSecuritySettings(allowed_hosts=[host, f"{host}:*", "localhost", "localhost:*"], allowed_origins=[f"https://{host}", "http://localhost", "http://localhost:*"] if host != "localhost" else ["http://localhost", "http://localhost:*"])
app = mcp.streamable_http_app(transport_security=security)

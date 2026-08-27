import base64
import hashlib
import os
import time
import uuid
from typing import Any

try:
    import env_bootstrap as _env_bootstrap  # noqa: F401
except ModuleNotFoundError:
    from services.mcp import env_bootstrap as _env_bootstrap  # noqa: F401

os.environ.setdefault("FASTMCP_STATELESS_HTTP", "true")
os.environ.setdefault("FASTMCP_JSON_RESPONSE", "true")
os.environ.setdefault("FASTMCP_STREAMABLE_HTTP_PATH", "/mcp")

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

ENGINE_URL = os.getenv("FABRIENT_ENGINE_URL", "https://fabrient-engineering.onrender.com").rstrip("/")
MCP_TIMEOUT = min(max(float(os.getenv("FABRIENT_MCP_TIMEOUT", "120")), 5.0), 300.0)
MAX_PAYLOAD_BYTES = 25_000_000
HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "fabrient-mcp.onrender.com")
TRANSPORT_SECURITY = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=[HOST, f"{HOST}:*"],
    allowed_origins=[f"https://{HOST}", f"https://{HOST}:*"]
)

mcp = FastMCP(
    "Fabrient Engineering",
    instructions="Fabrient MCP: deterministic engineering algorithms + measured-evidence ML + bounded engineering/LLM orchestration. Never invent measurements or confidence. Every tool returns or preserves evidence, status, and provenance where the engine supports it.",
    host=HOST,
    json_response=True,
    stateless_http=True,
    streamable_http_path="/mcp",
    transport_security=TRANSPORT_SECURITY,
)

CAPABILITY_REGISTRY = (
    ("inspect_part", "Inspect a part.", "/v1/toolbox/inspect_part"), ("analyze_dfm", "Analyze DFM.", "/v1/toolbox/analyze_dfm"), ("auto_fix_dfm", "Auto fix DFM.", "/v1/toolbox/auto_fix_dfm"), ("verify_fixes", "Verify fixes.", "/v1/toolbox/verify_fixes"), ("generate_manufacturing_package", "Generate manufacturing package.", "/v1/toolbox/generate_manufacturing_package"), ("generate_physical_build_guide", "Generate physical build guide.", "/v1/manufacturing/build-guide"), ("release_manufacturing_package", "Release manufacturing package.", "/v1/toolbox/release_manufacturing_package"), ("validate_material", "Validate material.", "/v1/toolbox/validate_material"), ("validate_machine_envelope", "Validate machine envelope.", "/v1/toolbox/validate_machine_envelope"), ("validate_dimension", "Validate a measured dimension against a nominal and tolerance.", "/v1/toolbox/validate_dimension"), ("check_wall_thickness", "Check wall thickness.", "/v1/toolbox/check_wall_thickness"), ("check_clearances", "Check clearances.", "/v1/toolbox/check_clearances"), ("check_holes", "Check holes.", "/v1/toolbox/check_holes"), ("check_overhangs", "Check overhangs.", "/v1/toolbox/check_overhangs"), ("check_bridges", "Check bridges.", "/v1/toolbox/check_bridges"), ("check_supports", "Check supports.", "/v1/toolbox/check_supports"), ("check_orientation", "Check orientation.", "/v1/toolbox/check_orientation"), ("check_tolerances", "Check tolerances.", "/v1/toolbox/check_tolerances"), ("check_fit", "Check fit.", "/v1/toolbox/check_fit"), ("check_warp_risk", "Check warp risk.", "/v1/toolbox/check_warp_risk"), ("check_first_layer", "Check first layer.", "/v1/toolbox/check_first_layer"), ("check_thermal_risk", "Check thermal risk.", "/v1/toolbox/check_thermal_risk"), ("check_print_time", "Check print time.", "/v1/toolbox/check_print_time"), ("check_material_usage", "Check material usage.", "/v1/toolbox/check_material_usage"), ("check_bed_adhesion", "Check bed adhesion.", "/v1/toolbox/check_bed_adhesion"), ("check_part_split", "Check part split.", "/v1/toolbox/check_part_split"), ("check_fastener_access", "Check fastener access.", "/v1/toolbox/check_fastener_access"), ("check_assembly_order", "Check assembly order.", "/v1/toolbox/check_assembly_order"), ("check_service_access", "Check service access.", "/v1/toolbox/check_service_access"), ("check_draft", "Check draft.", "/v1/toolbox/check_draft"), ("check_sharp_edges", "Check sharp edges.", "/v1/toolbox/check_sharp_edges"), ("check_small_features", "Check small features.", "/v1/toolbox/check_small_features"), ("check_text_legibility", "Check text legibility.", "/v1/toolbox/check_text_legibility"), ("check_embossed_features", "Check embossed features.", "/v1/toolbox/check_embossed_features"), ("check_threads", "Check threads.", "/v1/toolbox/check_threads"), ("check_press_fits", "Check press fits.", "/v1/toolbox/check_press_fits"), ("check_snap_fits", "Check snap fits.", "/v1/toolbox/check_snap_fits"), ("check_insert_pockets", "Check insert pockets.", "/v1/toolbox/check_insert_pockets"), ("check_connector_clearance", "Check connector clearance.", "/v1/toolbox/check_connector_clearance"), ("check_cable_clearance", "Check cable clearance.", "/v1/toolbox/check_cable_clearance"), ("check_pcb_clearance", "Check PCB clearance.", "/v1/toolbox/check_pcb_clearance"), ("check_component_keepouts", "Check component keepouts.", "/v1/toolbox/check_component_keepouts"), ("check_revision_consistency", "Check revision consistency.", "/v1/toolbox/check_revision_consistency"), ("compare_revisions", "Compare revisions.", "/v1/toolbox/compare_revisions"), ("trace_provenance", "Trace provenance.", "/v1/toolbox/trace_provenance"), ("build_inspection_plan", "Build inspection plan.", "/v1/toolbox/build_inspection_plan"), ("map_inspection_columns", "Map inspection columns.", "/v1/toolbox/map_inspection_columns"), ("calibrate_from_observations", "Calibrate from observations.", "/v1/toolbox/calibrate_from_observations"), ("estimate_risk", "Estimate risk.", "/v1/toolbox/estimate_risk"), ("calculate_reverification", "Calculate reverification.", "/v1/toolbox/calculate_reverification"), ("propose_next_experiment", "Propose next experiment.", "/v1/toolbox/propose_next_experiment"), ("run_bounded_engineering_review", "Run bounded engineering review.", "/v1/toolbox/run_bounded_engineering_review"), ("physics_predict", "Run deterministic physics prediction.", "/v1/predict"), ("simulation_run", "Run simulation.", "/v1/simulate"), ("calibration_fit", "Fit calibration from observations.", "/v1/calibrate"), ("uncertainty_calculate", "Calculate uncertainty.", "/v1/uncertainty"), ("acceptance_gate", "Run acceptance gate.", "/v1/acceptance"), ("reverification_calculate", "Calculate reverification.", "/v1/reverification"), ("next_experiment", "Select next experiment.", "/v1/next-experiment"), ("engineering_agent_run", "Run bounded engineering agent.", "/v1/agents/run"), ("dfm_analyze", "Run engineering DFM analysis.", "/v1/dfm/analyze"), ("dfm_self_fix", "Run engineering DFM self-fix.", "/v1/dfm/self-fix"), ("manufacturing_package", "Generate manufacturing package.", "/v1/manufacturing/package"), ("physical_build_guide", "Generate physical build guide.", "/v1/manufacturing/build-guide"), ("system_identification", "Run system identification.", "/v1/system-identification"), ("residual_uncertainty", "Calculate residual uncertainty.", "/v1/residual-uncertainty"), ("inspection_report_csv", "Generate inspection CSV report.", "/v1/inspection-report/csv"), ("inspection_report_pdf", "Generate inspection PDF report.", "/v1/inspection-report/pdf"), ("agent_graph", "Build agent graph.", "/v1/agent-graph"), ("agent_step", "Run one agent step.", "/v1/agent/step"), ("risk_estimate", "Estimate final risk.", "/v1/final/risk"), ("final_system_identification", "Run final system identification.", "/v1/final/system-identification"), ("cad_step_extract", "Extract supported STEP geometry; inspection only, never CAD generation.", "/v1/geometry/step"), ("cv_measure", "Measure geometry with computer vision.", "/v1/cv/measure"), ("inspection_preview", "Preview inspection import.", "/v1/import/preview"), ("inspection_confirm", "Confirm inspection import.", "/v1/final/import/confirm"), ("cv_measure_real", "Measure real millimetres using an explicit physical reference.", "/v1/cv/measure-real"), ("cv_detect_line_candidates", "Detect candidate image lines.", "/v1/cv/detect-line-candidates"), ("sim2real_run", "Run calibrated physics simulation.", "/v1/sim2real/run"), ("sim2real_compare", "Compare simulation with real residual evidence.", "/v1/sim2real/compare"), ("agent_fleet_run", "Run bounded engineering agent fleet.", "/v1/agents/fleet"), ("llm_engineering_critic", "Run optional bounded engineering critic.", "/v1/agents/fleet"), ("ml_machine_system_id", "Run ML machine system identification.", "/v1/system-identification"), ("deterministic_acceptance", "Run deterministic acceptance.", "/v1/acceptance"), ("sim2real_calibrate_and_run", "Run calibrated sim-to-real after held-out validation.", "/v1/sim2real/calibrate-and-run"), ("cv_measure_real_json", "Measure real millimetres from base64 image data.", "/v1/cv/measure-real-json"), ("manufacturing_release_candidate", "Generate manufacturing release candidate.", "/v1/manufacturing/package"), ("manufacturing_release_gate", "Run manufacturing release gate.", "/v1/toolbox/release_manufacturing_package"), ("manufacturing_dfm_fix_verify", "Fix and verify manufacturing DFM.", "/v1/dfm/self-fix"), ("manufacturing_inspection_plan", "Build manufacturing inspection plan.", "/v1/toolbox/build_inspection_plan"), ("manufacturing_provenance", "Return manufacturing provenance.", "/v1/toolbox/trace_provenance"), ("cad_manufacturing_risk", "Review supplied CAD/geometry manufacturing risk.", "/v1/toolbox/analyze_dfm"), ("cad_wall_clearance_review", "Review geometry wall and clearance risk.", "/v1/toolbox/check_wall_thickness"), ("cad_hole_review", "Review supplied geometry holes.", "/v1/toolbox/check_holes"), ("cad_overhang_review", "Review supplied geometry overhangs.", "/v1/toolbox/check_overhangs"), ("cad_bridge_review", "Review supplied geometry bridges.", "/v1/toolbox/check_bridges"), ("cad_tolerance_review", "Review supplied geometry tolerances.", "/v1/toolbox/check_tolerances"), ("risk_map", "Compute deterministic evidence-backed engineering risk map.", "/v1/risk-map"), ("ml_data_quality", "Review ML data quality.", "/v1/toolbox/check_data_quality"), ("ml_training_data_audit", "Audit ML training data.", "/v1/toolbox/audit_training_data"),
)
CAPABILITY_NAMES = [name for name, _, _ in CAPABILITY_REGISTRY]
TOOL_NAMES = CAPABILITY_NAMES
TOOL_COUNT = len(CAPABILITY_REGISTRY)
if TOOL_COUNT != 100 or len(set(CAPABILITY_NAMES)) != 100:
    raise RuntimeError(f"Authoritative MCP registry must contain exactly 100 unique tools; got {TOOL_COUNT}")
QUALITY_IMPROVEMENTS = ("stable_operation_identity", "bounded_timeout", "payload_size_guard", "strict_base64_validation_for_uploads", "normalized_error_reporting", "request_timing", "request_id_for_traceability", "input_fingerprint_for_reproducibility", "evidence_boundary_preservation", "structured_result_metadata")

async def _post(path: str, payload: dict[str, Any] | None = None, timeout: float | None = None, operation_name: str | None = None) -> Any:
    payload = dict(payload or {})
    operation = operation_name or path.rsplit("/", 1)[-1]
    request_id = uuid.uuid4().hex
    started = time.perf_counter()
    upload_paths = {"/v1/geometry/step", "/v1/cv/measure", "/v1/import/preview", "/v1/cv/measure-real", "/v1/cv/detect-line-candidates", "/v1/cv/measure-real-json"}
    payload_for_hash = {k: v for k, v in payload.items() if k != "file_base64"}
    input_fingerprint = hashlib.sha256(repr(sorted(payload_for_hash.items())).encode("utf-8")).hexdigest()[:16]
    request_timeout = min(max(float(timeout if timeout is not None else MCP_TIMEOUT), 5.0), 300.0)
    try:
        if path in upload_paths and payload.get("file_base64"):
            try:
                raw = base64.b64decode(payload["file_base64"], validate=True)
            except Exception as exc:
                raise ValueError("file_base64 must be valid base64") from exc
            if len(raw) > MAX_PAYLOAD_BYTES:
                raise ValueError("uploaded file exceeds 25 MB")
            filename = str(payload.get("filename") or "upload.bin")
            file_fields = {k: v for k, v in payload.items() if k not in {"file_base64", "filename"}}
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.post(f"{ENGINE_URL}{path}", files={"file": (filename, raw, "application/octet-stream")}, data=file_fields)
        else:
            request_body = {"operation": path.rsplit("/", 1)[-1], "payload": payload} if path.startswith("/v1/toolbox/") else payload
            async with httpx.AsyncClient(timeout=request_timeout) as client:
                response = await client.post(f"{ENGINE_URL}{path}", json=request_body)
        try:
            data = response.json()
        except Exception:
            data = {"content_type": response.headers.get("content-type", ""), "status_code": response.status_code, "text": response.text[:20000]}
        if response.status_code >= 400:
            raise RuntimeError(f"Engineering API {response.status_code}: {data}")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        if isinstance(data, dict):
            data.setdefault("_fabrient_meta", {})
            data["_fabrient_meta"].update({"operation": operation, "request_id": request_id, "input_fingerprint": input_fingerprint, "latency_ms": elapsed_ms, "quality_contract": list(QUALITY_IMPROVEMENTS), "evidence_policy": "no invented measurements or confidence"})
        return data
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        raise RuntimeError(f"Fabrient MCP request failed safely: operation={operation} request_id={request_id} latency_ms={elapsed_ms} cause={type(exc).__name__}") from exc

def _register(name: str, description: str, path: str) -> None:
    enhanced_description = f"{description} Quality contract: stable identity, bounded timeout, payload guards, normalized errors, trace ID, timing, reproducible input fingerprint, evidence boundary, and structured metadata."
    if name == "validate_dimension":
        async def tool(nominal_mm: float, measured_mm: float, tolerance_mm: float) -> Any:
            if tolerance_mm < 0:
                raise ValueError("tolerance_mm must be non-negative")
            deviation_mm = measured_mm - nominal_mm
            return {"accepted": abs(deviation_mm) <= tolerance_mm, "nominal_mm": nominal_mm, "measured_mm": measured_mm, "tolerance_mm": tolerance_mm, "deviation_mm": deviation_mm, "decision_basis": "abs(measured_mm - nominal_mm) <= tolerance_mm", "provenance": {"source": "mcp_deterministic_dimension_check", "synthetic": False}}
    else:
        async def tool(payload: dict[str, Any] | None = None) -> Any:
            return await _post(path, dict(payload or {}), operation_name=name)
    tool.__name__ = name
    tool.__doc__ = enhanced_description
    mcp.tool()(tool)

for _name, _description, _path in CAPABILITY_REGISTRY:
    _register(_name, _description, _path)

@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "fabrient-mcp", "engine_url": ENGINE_URL, "tool_count": TOOL_COUNT, "quality_contract": list(QUALITY_IMPROVEMENTS)})

@mcp.custom_route("/capabilities", methods=["GET"])
async def capabilities(_: Request) -> JSONResponse:
    return JSONResponse({"name": "Fabrient Engineering", "tool_count": TOOL_COUNT, "tools": CAPABILITY_NAMES, "engine_url": ENGINE_URL, "registry_authoritative": True, "quality_contract": list(QUALITY_IMPROVEMENTS)})

_mcp_app = mcp.streamable_http_app()

# The package entrypoint services.mcp.auth_server owns the single production
# auth wrapper. Keeping this module raw preserves the MCP SDK lifespan.
_mcp_app = _mcp_app


# FABRIENT_PRODUCTION_AUTH_WRAPPED
from services.mcp.production_auth import wrap_app as _fabrient_wrap_app
app = _fabrient_wrap_app(_mcp_app, CAPABILITY_REGISTRY)

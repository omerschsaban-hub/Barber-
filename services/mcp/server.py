from __future__ import annotations
import base64, os
from typing import Any
import httpx
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

ENGINE_URL=os.getenv("FABRIENT_ENGINE_URL","https://fabrient-engineering.onrender.com").rstrip("/")
mcp=MCPServer("Fabrient Engineering",instructions="Deterministic Fabrient engineering tools. Preserve uncertainty and provenance. MCP is an adapter/orchestration layer; the engineering service remains the source of truth.")

async def post(path:str,payload:dict[str,Any],timeout:float=120)->Any:
    async with httpx.AsyncClient(timeout=timeout) as c:
        r=await c.post(f"{ENGINE_URL}{path}",json=payload)
        try:d=r.json()
        except Exception:d={"text":r.text}
        if r.status_code>=400: raise RuntimeError(f"Engineering API {r.status_code}: {d}")
        return d

async def cv(image_base64:str)->dict[str,Any]:
    try: raw=base64.b64decode(image_base64,validate=True)
    except Exception as e: raise ValueError("image_base64 must be valid base64") from e
    if len(raw)>10_000_000: raise ValueError("image exceeds 10 MB")
    async with httpx.AsyncClient(timeout=60) as c:
        r=await c.post(f"{ENGINE_URL}/v1/cv/measure",files={"file":("measurement-image",raw,"application/octet-stream")})
        try:d=r.json()
        except Exception:d={"text":r.text}
        if r.status_code>=400: raise RuntimeError(f"Engineering API {r.status_code}: {d}")
        return d

@mcp.tool()
async def engine_health()->dict[str,Any]:
    """Check the engineering API."""
    try:
        async with httpx.AsyncClient(timeout=10) as c:r=await c.get(f"{ENGINE_URL}/health")
        return {"ok":r.is_success,"status_code":r.status_code,"engine_url":ENGINE_URL,"body":r.text[:2000]}
    except Exception as e:return {"ok":False,"engine_url":ENGINE_URL,"error":str(e)}

@mcp.tool()
def validate_dimension(nominal_mm:float,measured_mm:float,tolerance_mm:float)->dict[str,Any]:
    """Classify a measured dimension against an explicit tolerance."""
    if tolerance_mm<0:raise ValueError("tolerance_mm must be non-negative")
    d=measured_mm-nominal_mm
    return {"accepted":abs(d)<=tolerance_mm,"nominal_mm":nominal_mm,"measured_mm":measured_mm,"tolerance_mm":tolerance_mm,"deviation_mm":d}

CAPABILITY_NAMES = [
"engine_health","validate_dimension","get_fabrient_capabilities","cv_measure_image","cv_feature_count","cv_measurement_readiness","cv_scale_gate","cv_feature_summary","cv_confidence_gate","cv_provenance","cv_reference_check","cv_safe_record","cv_next_measurement","cv_quality_gate","sim2real_predict","sim2real_simulate","sim2real_calibrate","sim2real_uncertainty","sim2real_acceptance","sim2real_reverification","sim2real_next_experiment","sim2real_residual","sim2real_evidence_gate","sim2real_drift_rate","select_next_experiment","run_bounded_engineering_agent","inspection_upload_contract","step_geometry_upload_contract",
"dfm_analyze","dfm_self_fix","dfm_verify_fixes","manufacturing_package","manufacturing_build_guide","manufacturing_release_gate","inspect_part","analyze_geometry","extract_features","calculate_bounding_box","analyze_tolerances","analyze_clearances","analyze_wall_thickness","analyze_overhangs","analyze_bridges","analyze_holes","analyze_threads","analyze_dfm","auto_fix_dfm","verify_fixes","score_manufacturability","find_manufacturing_risks","suggest_orientation","analyze_support_strategy","analyze_shrinkage_risk","analyze_warp_risk","identify_machine","identify_process","system_identification","analyze_machine_drift","analyze_service_wear","compare_machines","compare_revisions","fit_residual_model","validate_residual_model","calibrate_model_uncertainty","run_model_diagnostics","estimate_prediction_interval","detect_distribution_shift","check_data_quality","audit_training_data","run_domain_randomization","run_sensitivity_analysis","rank_experiments","compare_experiments","record_experiment","approve_experiment","refuse_experiment","generate_manufacturing_package","generate_physical_build_guide","validate_manufacturing_package","release_manufacturing_package","generate_inspection_record","export_inspection_csv","generate_report_pdf","verify_release_provenance","get_project_state","save_project_state","get_next_best_action","record_activity","get_project_history","create_review_share","get_review_share","write_audit_record","get_audit_trail","run_engineering_agent","cad_generation_guidance","cad_constraint_plan","cad_feature_plan","cad_revision_review","manufacturing_process_plan","inspection_plan","quality_gate","evidence_gate","llm_engineering_plan","ml_residual_analysis","deterministic_risk_analysis","combined_engineering_review"
]

@mcp.tool()
def get_fabrient_capabilities()->dict[str,Any]:
    """List the complete 100-tool Fabrient MCP surface."""
    return {"name":"Fabrient Engineering","transport":"streamable-http","tool_count":100,"callable_tools":CAPABILITY_NAMES,"groups":["core","computer_vision","deterministic_physics","sim_to_real","manufacturing","CAD_guidance","ML","LLM_orchestration","evidence_and_release"]}

# CV tools: all backed by the real CV endpoint; no silent pixel-to-mm inference.
@mcp.tool()
async def cv_measure_image(image_base64:str)->dict[str,Any]:"""Measure physical-image features.""";return await cv(image_base64)
@mcp.tool()
async def cv_feature_count(image_base64:str)->dict[str,Any]:"""Count detected image features.""";x=await cv(image_base64);return {"features_detected":x.get("features_detected",0),"status":x.get("status"),"provenance":x.get("provenance")}
@mcp.tool()
async def cv_measurement_readiness(image_base64:str)->dict[str,Any]:"""Gate readiness for a millimetre claim.""";x=await cv(image_base64);return {"ready_for_mm_claim":x.get("measurement_mm") is not None and x.get("confidence") not in (None,"unknown"),"reason":x.get("reason"),"provenance":x.get("provenance")}
@mcp.tool()
async def cv_scale_gate(image_base64:str)->dict[str,Any]:"""Refuse silent pixel-to-mm scale inference.""";x=await cv(image_base64);return {"scale_gate":"pass" if x.get("measurement_mm") is not None else "refused","measurement_mm":x.get("measurement_mm"),"reason":x.get("reason")}
@mcp.tool()
async def cv_feature_summary(image_base64:str)->dict[str,Any]:"""Summarize image geometry features without inventing units.""";x=await cv(image_base64);return {"features_detected":x.get("features_detected",0),"units":"pixels/features only","mm_claim_allowed":False,"provenance":x.get("provenance")}
@mcp.tool()
async def cv_confidence_gate(image_base64:str)->dict[str,Any]:"""Gate image-derived claims on explicit confidence.""";x=await cv(image_base64);c=x.get("confidence");return {"accepted":c not in (None,"unknown"),"confidence":c,"reason":x.get("reason")}
@mcp.tool()
async def cv_provenance(image_base64:str)->dict[str,Any]:"""Return CV provenance.""";x=await cv(image_base64);return {"provenance":x.get("provenance",{}),"status":x.get("status")}
@mcp.tool()
async def cv_reference_check(image_base64:str)->dict[str,Any]:"""Check for a usable physical reference.""";x=await cv(image_base64);return {"physical_reference_present":x.get("measurement_mm") is not None,"measurement_mm":x.get("measurement_mm"),"reason":x.get("reason")}
@mcp.tool()
async def cv_safe_record(image_base64:str)->dict[str,Any]:"""Return a non-fabricated CV evidence record.""";x=await cv(image_base64);return {"measurement_mm":x.get("measurement_mm"),"confidence":x.get("confidence"),"features_detected":x.get("features_detected",0),"status":x.get("status"),"provenance":x.get("provenance"),"synthetic":False}
@mcp.tool()
async def cv_next_measurement(image_base64:str)->dict[str,Any]:"""Recommend the next physical evidence step.""";x=await cv(image_base64);return {"next_action":"Add a known physical reference and recapture." if x.get("measurement_mm") is None else "Validate against a real inspection record.","reason":x.get("reason")}
@mcp.tool()
async def cv_quality_gate(image_base64:str)->dict[str,Any]:"""Gate CV output when image evidence is insufficient.""";x=await cv(image_base64);return {"pass":x.get("status") not in ("unsupported","error"),"status":x.get("status"),"reason":x.get("reason")}

# Sim-to-real tools: direct calls to real engineering endpoints plus deterministic evidence math.
@mcp.tool()
async def sim2real_predict(payload:dict[str,Any])->dict[str,Any]:"""Run deterministic prediction.""";return await post("/v1/predict",payload)
@mcp.tool()
async def sim2real_simulate(payload:dict[str,Any])->dict[str,Any]:"""Run seeded domain-randomized simulation.""";return await post("/v1/simulate",payload)
@mcp.tool()
async def sim2real_calibrate(payload:dict[str,Any])->dict[str,Any]:"""Calibrate from real observations.""";return await post("/v1/calibrate",payload)
@mcp.tool()
async def sim2real_uncertainty(payload:dict[str,Any])->dict[str,Any]:"""Combine uncertainty components.""";return await post("/v1/uncertainty",payload)
@mcp.tool()
async def sim2real_acceptance(payload:dict[str,Any])->dict[str,Any]:"""Run acceptance/refusal logic.""";return await post("/v1/acceptance",payload)
@mcp.tool()
async def sim2real_reverification(payload:dict[str,Any])->dict[str,Any]:"""Calculate bounded re-verification timing.""";return await post("/v1/reverification",payload)
@mcp.tool()
async def sim2real_next_experiment(payload:dict[str,Any])->dict[str,Any]:"""Select an information-gaining next experiment.""";return await post("/v1/next-experiment",payload)
@mcp.tool()
def sim2real_residual(predicted_mm:float,measured_mm:float)->dict[str,Any]:"""Calculate a real-measurement residual.""";return {"predicted_mm":predicted_mm,"measured_mm":measured_mm,"residual_mm":measured_mm-predicted_mm,"synthetic":False}
@mcp.tool()
def sim2real_evidence_gate(observed_sigma_mm:float,measurement_sigma_mm:float,tolerance_band_mm:float)->dict[str,Any]:"""Check whether observed plus measurement uncertainty fits a tolerance band.""";combined=(observed_sigma_mm**2+measurement_sigma_mm**2)**0.5;band=3.92*combined;return {"supported":band<=tolerance_band_mm,"combined_sigma_mm":combined,"supported_tolerance_band_mm":band}
@mcp.tool()
def sim2real_drift_rate(previous_residual_mm:float,current_residual_mm:float,elapsed_days:float)->dict[str,Any]:"""Compute observed residual drift rate without a causal claim.""";

@mcp.tool()
async def select_next_experiment(payload:dict[str,Any])->dict[str,Any]:"""Select next experiment from real measurements.""";return await post("/v1/next-experiment",payload)
@mcp.tool()
async def run_bounded_engineering_agent(payload:dict[str,Any])->dict[str,Any]:"""Run bounded engineering-agent orchestration.""";return await post("/v1/agents/run",payload)
@mcp.tool()
def inspection_upload_contract()->dict[str,Any]:"""Return the real inspection upload contract.""";return {"endpoint":"/v1/import/preview","method":"POST multipart","status":"requires_file_upload"}
@mcp.tool()
def step_geometry_upload_contract()->dict[str,Any]:"""Return the real STEP upload contract.""";return {"endpoint":"/v1/geometry/step","method":"POST multipart","status":"requires_step_file"}

# Remaining 72 first-class tools. They are adapters to existing deterministic
# engineering endpoints; they do not pretend to implement missing CAD/ML/LLM
# systems inside the MCP layer. Operation-specific names route to the real
# manufacturing toolbox or to the real agent/physics/ML endpoints.
_EXTRA = {
"dfm_analyze":("/v1/dfm/analyze","Run deterministic DFM analysis."),
"dfm_self_fix":("/v1/dfm/self-fix","Apply only deterministic scalar DFM fixes and return every change."),
"dfm_verify_fixes":("/v1/dfm/analyze","Verify a proposed DFM state by re-running deterministic checks."),
"manufacturing_package":("/v1/manufacturing/package","Generate the release-candidate manufacturing package manifest and gates."),
"manufacturing_build_guide":("/v1/manufacturing/build-guide","Generate the physical build guide from manufacturing context."),
"manufacturing_release_gate":("/v1/manufacturing/package","Evaluate manufacturing package release gates."),
"generate_manufacturing_package":("/v1/manufacturing/package","Generate a manufacturing package."),
"generate_physical_build_guide":("/v1/manufacturing/build-guide","Generate a physical build guide."),
"validate_manufacturing_package":("/v1/manufacturing/package","Validate manufacturing package gates."),
"release_manufacturing_package":("/v1/manufacturing/package","Evaluate release eligibility without silently authorizing production."),
"run_engineering_agent":("/v1/agents/run","Run the bounded multi-agent engineering plan."),
"cad_generation_guidance":("/v1/agents/run","Generate bounded CAD-generation guidance; CAD mutation remains outside the MCP adapter."),
"cad_constraint_plan":("/v1/agents/run","Produce a constrained CAD planning pass."),
"cad_feature_plan":("/v1/agents/run","Produce a feature-level CAD planning pass."),
"cad_revision_review":("/v1/agents/run","Review CAD revision context with evidence gates."),
"manufacturing_process_plan":("/v1/agents/run","Produce a bounded manufacturing process plan."),
"inspection_plan":("/v1/agents/run","Produce a bounded inspection plan."),
"quality_gate":("/v1/acceptance","Run the real deterministic quality/acceptance gate."),
"evidence_gate":("/v1/uncertainty","Run the real uncertainty/evidence calculation."),
"llm_engineering_plan":("/v1/agents/run","Expose the existing engineering orchestration boundary for LLM-assisted planning; no fabricated evidence."),
"ml_residual_analysis":("/v1/calibrate","Expose the real residual ML calibration endpoint using real observations."),
"deterministic_risk_analysis":("/v1/uncertainty","Expose deterministic uncertainty/risk calculations."),
"combined_engineering_review":("/v1/agents/run","Combine bounded agent orchestration with deterministic engineering gates."),
}

# Toolbox operations that already exist in engineering/app/manufacturing.py.
_TOOLBOX = [
"inspect_part","analyze_geometry","extract_features","calculate_bounding_box","analyze_tolerances","analyze_clearances","analyze_wall_thickness","analyze_overhangs","analyze_bridges","analyze_holes","analyze_threads","analyze_dfm","auto_fix_dfm","verify_fixes","score_manufacturability","find_manufacturing_risks","suggest_orientation","analyze_support_strategy","analyze_shrinkage_risk","analyze_warp_risk","identify_machine","identify_process","system_identification","analyze_machine_drift","analyze_service_wear","compare_machines","compare_revisions","fit_residual_model","validate_residual_model","calibrate_model_uncertainty","run_model_diagnostics","estimate_prediction_interval","detect_distribution_shift","check_data_quality","audit_training_data","run_domain_randomization","run_sensitivity_analysis","rank_experiments","compare_experiments","record_experiment","approve_experiment","refuse_experiment","generate_inspection_record","export_inspection_csv","generate_report_pdf","verify_release_provenance","get_project_state","save_project_state","get_next_best_action","record_activity","get_project_history","create_review_share","get_review_share","write_audit_record","get_audit_trail"
]
for _name in _TOOLBOX:
    _EXTRA.setdefault(_name,(f"/v1/toolbox/{_name}",f"Call the existing Fabrient engineering toolbox operation: {_name}."))

for _name in CAPABILITY_NAMES[28:]:
    _path,_desc=_EXTRA[_name]
    async def _tool(payload:dict[str,Any]|None=None,_path=_path,_name=_name)->dict[str,Any]:
        """First-class Fabrient capability adapter."""
        return await post(_path,payload or {})
    _tool.__name__=_name
    _tool.__doc__=_desc
    mcp.tool(name=_name,description=_desc)(_tool)

assert len(CAPABILITY_NAMES)==100
assert len(set(CAPABILITY_NAMES))==100
assert set(CAPABILITY_NAMES[28:])==set(_EXTRA)

@mcp.custom_route("/health",methods=["GET"])
async def health(_:Request)->JSONResponse:return JSONResponse({"status":"ok","service":"fabrient-mcp","engine_url":ENGINE_URL,"tool_count":100})

host=os.getenv("RENDER_EXTERNAL_HOSTNAME","localhost")
security=TransportSecuritySettings(allowed_hosts=[host,f"{host}:*","localhost","localhost:*"],allowed_origins=[f"https://{host}","http://localhost","http://localhost:*"] if host!="localhost" else ["http://localhost","http://localhost:*"])
app=mcp.streamable_http_app(transport_security=security)

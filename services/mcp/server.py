from __future__ import annotations

import base64
import os
from typing import Any
import httpx
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

ENGINE_URL=os.getenv("FABRIENT_ENGINE_URL","https://fabrient-engineering.onrender.com").rstrip("/")
mcp=MCPServer("Fabrient Engineering",instructions="Fabrient MCP: deterministic engineering algorithms + measured-evidence ML + bounded engineering/LLM orchestration. Never invent measurements or confidence.")

async def _post(path: str, payload: dict[str, Any] | None = None, timeout: float = 120) -> Any:
    payload=payload or {}
    upload_paths={"/v1/geometry/step","/v1/cv/measure","/v1/import/preview"}
    if path in upload_paths and payload.get("file_base64"):
        try: raw=base64.b64decode(payload["file_base64"], validate=True)
        except Exception as e: raise ValueError("file_base64 must be valid base64") from e
        if len(raw)>25_000_000: raise ValueError("uploaded file exceeds 25 MB")
        filename=str(payload.get("filename") or "upload.bin")
        extra={k:v for k,v in payload.items() if k not in {"file_base64","filename"}}
        async with httpx.AsyncClient(timeout=timeout) as c: r=await c.post(f"{ENGINE_URL}{path}",files={"file":(filename,raw,"application/octet-stream")},data=extra)
    else:
        async with httpx.AsyncClient(timeout=timeout) as c: r=await c.post(f"{ENGINE_URL}{path}",json=payload)
    try: data=r.json()
    except Exception: data={"content_type":r.headers.get("content-type",""),"status_code":r.status_code,"text":r.text[:20000]}
    if r.status_code>=400: raise RuntimeError(f"Engineering API {r.status_code}: {data}")
    return data

TOOL_COUNT=100
TOOL_NAMES=['inspect_part', 'analyze_dfm', 'auto_fix_dfm', 'verify_fixes', 'generate_manufacturing_package', 'generate_physical_build_guide', 'release_manufacturing_package', 'validate_material', 'validate_machine_envelope', 'check_wall_thickness', 'check_clearances', 'check_holes', 'check_overhangs', 'check_bridges', 'check_supports', 'check_orientation', 'check_tolerances', 'check_fit', 'check_warp_risk', 'check_first_layer', 'check_thermal_risk', 'check_print_time', 'check_material_usage', 'check_bed_adhesion', 'check_part_split', 'check_fastener_access', 'check_assembly_order', 'check_service_access', 'check_draft', 'check_sharp_edges', 'check_small_features', 'check_text_legibility', 'check_embossed_features', 'check_threads', 'check_press_fits', 'check_snap_fits', 'check_insert_pockets', 'check_connector_clearance', 'check_cable_clearance', 'check_pcb_clearance', 'check_component_keepouts', 'check_revision_consistency', 'compare_revisions', 'trace_provenance', 'build_inspection_plan', 'map_inspection_columns', 'calibrate_from_observations', 'estimate_risk', 'calculate_reverification', 'propose_next_experiment', 'run_bounded_engineering_review', 'physics_predict', 'simulation_run', 'calibration_fit', 'uncertainty_calculate', 'acceptance_gate', 'reverification_calculate', 'next_experiment', 'engineering_agent_run', 'dfm_analyze', 'dfm_self_fix', 'manufacturing_package', 'physical_build_guide', 'system_identification', 'residual_uncertainty', 'inspection_report_csv', 'inspection_report_pdf', 'agent_graph', 'agent_step', 'risk_estimate', 'final_system_identification', 'cad_step_extract', 'cv_measure', 'inspection_preview', 'inspection_confirm', 'physics_interval', 'physics_provenance', 'simulation_domain_randomization', 'simulation_seeded_repeat', 'ml_residual_fit', 'ml_residual_validation', 'ml_prediction_uncertainty', 'ml_machine_system_id', 'deterministic_acceptance', 'deterministic_reverification', 'deterministic_next_experiment', 'manufacturing_release_candidate', 'manufacturing_release_gate', 'manufacturing_dfm_fix_verify', 'manufacturing_inspection_plan', 'manufacturing_provenance', 'cad_manufacturing_risk', 'cad_wall_clearance_review', 'cad_hole_review', 'cad_overhang_review', 'cad_bridge_review', 'cad_tolerance_review', 'cad_fit_review', 'ml_data_quality', 'ml_training_data_audit']

def _register(name: str, description: str, path: str):
    async def tool(payload: dict[str, Any] | None = None) -> Any:
        return await _post(path,payload or {})
    tool.__name__=name; tool.__doc__=description; mcp.tool()(tool)

_register('inspect_part','Existing Fabrient toolbox capability: inspect part','/v1/toolbox/inspect_part')
_register('analyze_dfm','Existing Fabrient toolbox capability: analyze dfm','/v1/toolbox/analyze_dfm')
_register('auto_fix_dfm','Existing Fabrient toolbox capability: auto fix dfm','/v1/toolbox/auto_fix_dfm')
_register('verify_fixes','Existing Fabrient toolbox capability: verify fixes','/v1/toolbox/verify_fixes')
_register('generate_manufacturing_package','Existing Fabrient toolbox capability: generate manufacturing package','/v1/toolbox/generate_manufacturing_package')
_register('generate_physical_build_guide','Existing Fabrient toolbox capability: generate physical build guide','/v1/toolbox/generate_physical_build_guide')
_register('release_manufacturing_package','Existing Fabrient toolbox capability: release manufacturing package','/v1/toolbox/release_manufacturing_package')
_register('validate_material','Existing Fabrient toolbox capability: validate material','/v1/toolbox/validate_material')
_register('validate_machine_envelope','Existing Fabrient toolbox capability: validate machine envelope','/v1/toolbox/validate_machine_envelope')
_register('check_wall_thickness','Existing Fabrient toolbox capability: check wall thickness','/v1/toolbox/check_wall_thickness')
_register('check_clearances','Existing Fabrient toolbox capability: check clearances','/v1/toolbox/check_clearances')
_register('check_holes','Existing Fabrient toolbox capability: check holes','/v1/toolbox/check_holes')
_register('check_overhangs','Existing Fabrient toolbox capability: check overhangs','/v1/toolbox/check_overhangs')
_register('check_bridges','Existing Fabrient toolbox capability: check bridges','/v1/toolbox/check_bridges')
_register('check_supports','Existing Fabrient toolbox capability: check supports','/v1/toolbox/check_supports')
_register('check_orientation','Existing Fabrient toolbox capability: check orientation','/v1/toolbox/check_orientation')
_register('check_tolerances','Existing Fabrient toolbox capability: check tolerances','/v1/toolbox/check_tolerances')
_register('check_fit','Existing Fabrient toolbox capability: check fit','/v1/toolbox/check_fit')
_register('check_warp_risk','Existing Fabrient toolbox capability: check warp risk','/v1/toolbox/check_warp_risk')
_register('check_first_layer','Existing Fabrient toolbox capability: check first layer','/v1/toolbox/check_first_layer')
_register('check_thermal_risk','Existing Fabrient toolbox capability: check thermal risk','/v1/toolbox/check_thermal_risk')
_register('check_print_time','Existing Fabrient toolbox capability: check print time','/v1/toolbox/check_print_time')
_register('check_material_usage','Existing Fabrient toolbox capability: check material usage','/v1/toolbox/check_material_usage')
_register('check_bed_adhesion','Existing Fabrient toolbox capability: check bed adhesion','/v1/toolbox/check_bed_adhesion')
_register('check_part_split','Existing Fabrient toolbox capability: check part split','/v1/toolbox/check_part_split')
_register('check_fastener_access','Existing Fabrient toolbox capability: check fastener access','/v1/toolbox/check_fastener_access')
_register('check_assembly_order','Existing Fabrient toolbox capability: check assembly order','/v1/toolbox/check_assembly_order')
_register('check_service_access','Existing Fabrient toolbox capability: check service access','/v1/toolbox/check_service_access')
_register('check_draft','Existing Fabrient toolbox capability: check draft','/v1/toolbox/check_draft')
_register('check_sharp_edges','Existing Fabrient toolbox capability: check sharp edges','/v1/toolbox/check_sharp_edges')
_register('check_small_features','Existing Fabrient toolbox capability: check small features','/v1/toolbox/check_small_features')
_register('check_text_legibility','Existing Fabrient toolbox capability: check text legibility','/v1/toolbox/check_text_legibility')
_register('check_embossed_features','Existing Fabrient toolbox capability: check embossed features','/v1/toolbox/check_embossed_features')
_register('check_threads','Existing Fabrient toolbox capability: check threads','/v1/toolbox/check_threads')
_register('check_press_fits','Existing Fabrient toolbox capability: check press fits','/v1/toolbox/check_press_fits')
_register('check_snap_fits','Existing Fabrient toolbox capability: check snap fits','/v1/toolbox/check_snap_fits')
_register('check_insert_pockets','Existing Fabrient toolbox capability: check insert pockets','/v1/toolbox/check_insert_pockets')
_register('check_connector_clearance','Existing Fabrient toolbox capability: check connector clearance','/v1/toolbox/check_connector_clearance')
_register('check_cable_clearance','Existing Fabrient toolbox capability: check cable clearance','/v1/toolbox/check_cable_clearance')
_register('check_pcb_clearance','Existing Fabrient toolbox capability: check pcb clearance','/v1/toolbox/check_pcb_clearance')
_register('check_component_keepouts','Existing Fabrient toolbox capability: check component keepouts','/v1/toolbox/check_component_keepouts')
_register('check_revision_consistency','Existing Fabrient toolbox capability: check revision consistency','/v1/toolbox/check_revision_consistency')
_register('compare_revisions','Existing Fabrient toolbox capability: compare revisions','/v1/toolbox/compare_revisions')
_register('trace_provenance','Existing Fabrient toolbox capability: trace provenance','/v1/toolbox/trace_provenance')
_register('build_inspection_plan','Existing Fabrient toolbox capability: build inspection plan','/v1/toolbox/build_inspection_plan')
_register('map_inspection_columns','Existing Fabrient toolbox capability: map inspection columns','/v1/toolbox/map_inspection_columns')
_register('calibrate_from_observations','Existing Fabrient toolbox capability: calibrate from observations','/v1/toolbox/calibrate_from_observations')
_register('estimate_risk','Existing Fabrient toolbox capability: estimate risk','/v1/toolbox/estimate_risk')
_register('calculate_reverification','Existing Fabrient toolbox capability: calculate reverification','/v1/toolbox/calculate_reverification')
_register('propose_next_experiment','Existing Fabrient toolbox capability: propose next experiment','/v1/toolbox/propose_next_experiment')
_register('run_bounded_engineering_review','Existing Fabrient toolbox capability: run bounded engineering review','/v1/toolbox/run_bounded_engineering_review')
_register('physics_predict','Existing Fabrient engineering endpoint: /v1/predict','/v1/predict')
_register('simulation_run','Existing Fabrient engineering endpoint: /v1/simulate','/v1/simulate')
_register('calibration_fit','Existing Fabrient engineering endpoint: /v1/calibrate','/v1/calibrate')
_register('uncertainty_calculate','Existing Fabrient engineering endpoint: /v1/uncertainty','/v1/uncertainty')
_register('acceptance_gate','Existing Fabrient engineering endpoint: /v1/acceptance','/v1/acceptance')
_register('reverification_calculate','Existing Fabrient engineering endpoint: /v1/reverification','/v1/reverification')
_register('next_experiment','Existing Fabrient engineering endpoint: /v1/next-experiment','/v1/next-experiment')
_register('engineering_agent_run','Existing Fabrient engineering endpoint: /v1/agents/run','/v1/agents/run')
_register('dfm_analyze','Existing Fabrient engineering endpoint: /v1/dfm/analyze','/v1/dfm/analyze')
_register('dfm_self_fix','Existing Fabrient engineering endpoint: /v1/dfm/self-fix','/v1/dfm/self-fix')
_register('manufacturing_package','Existing Fabrient engineering endpoint: /v1/manufacturing/package','/v1/manufacturing/package')
_register('physical_build_guide','Existing Fabrient engineering endpoint: /v1/manufacturing/build-guide','/v1/manufacturing/build-guide')
_register('system_identification','Existing Fabrient engineering endpoint: /v1/system-identification','/v1/system-identification')
_register('residual_uncertainty','Existing Fabrient engineering endpoint: /v1/residual-uncertainty','/v1/residual-uncertainty')
_register('inspection_report_csv','Existing Fabrient engineering endpoint: /v1/inspection-report/csv','/v1/inspection-report/csv')
_register('inspection_report_pdf','Existing Fabrient engineering endpoint: /v1/inspection-report/pdf','/v1/inspection-report/pdf')
_register('agent_graph','Existing Fabrient engineering endpoint: /v1/agent-graph','/v1/agent-graph')
_register('agent_step','Existing Fabrient engineering endpoint: /v1/agent/step','/v1/agent/step')
_register('risk_estimate','Existing Fabrient engineering endpoint: /v1/final/risk','/v1/final/risk')
_register('final_system_identification','Existing Fabrient engineering endpoint: /v1/final/system-identification','/v1/final/system-identification')
_register('cad_step_extract','Existing Fabrient capability adapter: /v1/geometry/step','/v1/geometry/step')
_register('cv_measure','Existing Fabrient capability adapter: /v1/cv/measure','/v1/cv/measure')
_register('inspection_preview','Existing Fabrient capability adapter: /v1/import/preview','/v1/import/preview')
_register('inspection_confirm','Existing Fabrient capability adapter: /v1/final/import/confirm','/v1/final/import/confirm')
_register('physics_interval','Existing Fabrient capability adapter: /v1/predict','/v1/predict')
_register('physics_provenance','Existing Fabrient capability adapter: /v1/predict','/v1/predict')
_register('simulation_domain_randomization','Existing Fabrient capability adapter: /v1/simulate','/v1/simulate')
_register('simulation_seeded_repeat','Existing Fabrient capability adapter: /v1/simulate','/v1/simulate')
_register('ml_residual_fit','Existing Fabrient capability adapter: /v1/calibrate','/v1/calibrate')
_register('ml_residual_validation','Existing Fabrient capability adapter: /v1/calibrate','/v1/calibrate')
_register('ml_prediction_uncertainty','Existing Fabrient capability adapter: /v1/residual-uncertainty','/v1/residual-uncertainty')
_register('ml_machine_system_id','Existing Fabrient capability adapter: /v1/system-identification','/v1/system-identification')
_register('deterministic_acceptance','Existing Fabrient capability adapter: /v1/acceptance','/v1/acceptance')
_register('deterministic_reverification','Existing Fabrient capability adapter: /v1/reverification','/v1/reverification')
_register('deterministic_next_experiment','Existing Fabrient capability adapter: /v1/next-experiment','/v1/next-experiment')
_register('manufacturing_release_candidate','Existing Fabrient capability adapter: /v1/manufacturing/package','/v1/manufacturing/package')
_register('manufacturing_release_gate','Existing Fabrient capability adapter: /v1/toolbox/release_manufacturing_package','/v1/toolbox/release_manufacturing_package')
_register('manufacturing_dfm_fix_verify','Existing Fabrient capability adapter: /v1/dfm/self-fix','/v1/dfm/self-fix')
_register('manufacturing_inspection_plan','Existing Fabrient capability adapter: /v1/toolbox/build_inspection_plan','/v1/toolbox/build_inspection_plan')
_register('manufacturing_provenance','Existing Fabrient capability adapter: /v1/toolbox/trace_provenance','/v1/toolbox/trace_provenance')
_register('cad_manufacturing_risk','Existing Fabrient capability adapter: /v1/toolbox/analyze_dfm','/v1/toolbox/analyze_dfm')
_register('cad_wall_clearance_review','Existing Fabrient capability adapter: /v1/toolbox/check_wall_thickness','/v1/toolbox/check_wall_thickness')
_register('cad_hole_review','Existing Fabrient capability adapter: /v1/toolbox/check_holes','/v1/toolbox/check_holes')
_register('cad_overhang_review','Existing Fabrient capability adapter: /v1/toolbox/check_overhangs','/v1/toolbox/check_overhangs')
_register('cad_bridge_review','Existing Fabrient capability adapter: /v1/toolbox/check_bridges','/v1/toolbox/check_bridges')
_register('cad_tolerance_review','Existing Fabrient capability adapter: /v1/toolbox/check_tolerances','/v1/toolbox/check_tolerances')
_register('cad_fit_review','Existing Fabrient capability adapter: /v1/toolbox/check_fit','/v1/toolbox/check_fit')
_register('ml_data_quality','Existing Fabrient capability adapter: /v1/toolbox/check_data_quality','/v1/toolbox/check_data_quality')
_register('ml_training_data_audit','Existing Fabrient capability adapter: /v1/toolbox/audit_training_data','/v1/toolbox/audit_training_data')

@mcp.tool()
async def engine_health()->dict[str,Any]:
    try:
        async with httpx.AsyncClient(timeout=10) as c:r=await c.get(f"{ENGINE_URL}/health")
        return {"ok":r.is_success,"status_code":r.status_code,"engine_url":ENGINE_URL,"body":r.text[:2000]}
    except Exception as e:return {"ok":False,"engine_url":ENGINE_URL,"error":str(e)}

@mcp.tool()
def get_fabrient_capabilities()->dict[str,Any]:
    return {"name":"Fabrient Engineering","tool_count":TOOL_COUNT,"tools":TOOL_NAMES,"engine_url":ENGINE_URL,"groups":["deterministic_physics","dfm","cad","computer_vision","simulation","ml","manufacturing","inspection","provenance","bounded_agent_orchestration"]}

@mcp.custom_route("/health",methods=["GET"])
async def health(_:Request)->JSONResponse:
    return JSONResponse({"status":"ok","service":"fabrient-mcp","engine_url":ENGINE_URL,"tool_count":TOOL_COUNT})

host=os.getenv("RENDER_EXTERNAL_HOSTNAME","localhost")
security=TransportSecuritySettings(allowed_hosts=[host,f"{host}:*","localhost","localhost:*"],allowed_origins=[f"https://{host}","http://localhost","http://localhost:*"] if host!="localhost" else ["http://localhost","http://localhost:*"])
app=mcp.streamable_http_app(transport_security=security)


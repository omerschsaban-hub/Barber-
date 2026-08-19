from __future__ import annotations
import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

ENGINEERING_API = os.getenv("FABRIENT_ENGINEERING_API", "http://localhost:8000").rstrip("/")
mcp = FastMCP("Fabrient Engineering")

async def _request(method: str, path: str, *, json: Any = None, files: Any = None, params: Any = None, timeout: float = 120.0) -> Any:
    if not path.startswith("/") or path.startswith("//") or (not path.startswith("/v1/") and path not in {"/health", "/openapi.json"}):
        raise ValueError("Only Fabrient engineering API paths are permitted")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.request(method.upper(), f"{ENGINEERING_API}{path}", json=json, files=files, params=params)
        try: data = r.json()
        except Exception: data = {"text": r.text}
        if r.status_code >= 400: raise RuntimeError(f"Engineering API {r.status_code}: {data}")
        return data

TOOL_DESCRIPTIONS = {
    "inspect_part": "Fabrient manufacturing lifecycle tool: inspect part.",
    "analyze_dfm": "Fabrient manufacturing lifecycle tool: analyze dfm.",
    "auto_fix_dfm": "Fabrient manufacturing lifecycle tool: auto fix dfm.",
    "verify_fixes": "Fabrient manufacturing lifecycle tool: verify fixes.",
    "generate_manufacturing_package": "Fabrient manufacturing lifecycle tool: generate manufacturing package.",
    "generate_physical_build_guide": "Fabrient manufacturing lifecycle tool: generate a simple step-by-step physical build guide.",
    "release_manufacturing_package": "Fabrient manufacturing lifecycle tool: release manufacturing package.",
    "validate_material": "Fabrient manufacturing lifecycle tool: validate material.",
    "validate_machine_envelope": "Fabrient manufacturing lifecycle tool: validate machine envelope.",
    "check_wall_thickness": "Fabrient manufacturing lifecycle tool: check wall thickness.",
    "check_clearances": "Fabrient manufacturing lifecycle tool: check clearances.",
    "check_holes": "Fabrient manufacturing lifecycle tool: check holes.",
    "check_overhangs": "Fabrient manufacturing lifecycle tool: check overhangs.",
    "check_bridges": "Fabrient manufacturing lifecycle tool: check bridges.",
    "check_supports": "Fabrient manufacturing lifecycle tool: check supports.",
    "check_orientation": "Fabrient manufacturing lifecycle tool: check orientation.",
    "check_tolerances": "Fabrient manufacturing lifecycle tool: check tolerances.",
    "check_fit": "Fabrient manufacturing lifecycle tool: check fit.",
    "check_warp_risk": "Fabrient manufacturing lifecycle tool: check warp risk.",
    "check_first_layer": "Fabrient manufacturing lifecycle tool: check first layer.",
    "check_thermal_risk": "Fabrient manufacturing lifecycle tool: check thermal risk.",
    "check_print_time": "Fabrient manufacturing lifecycle tool: check print time.",
    "check_material_usage": "Fabrient manufacturing lifecycle tool: check material usage.",
    "check_bed_adhesion": "Fabrient manufacturing lifecycle tool: check bed adhesion.",
    "check_part_split": "Fabrient manufacturing lifecycle tool: check part split.",
    "check_fastener_access": "Fabrient manufacturing lifecycle tool: check fastener access.",
    "check_assembly_order": "Fabrient manufacturing lifecycle tool: check assembly order.",
    "check_service_access": "Fabrient manufacturing lifecycle tool: check service access.",
    "check_draft": "Fabrient manufacturing lifecycle tool: check draft.",
    "check_sharp_edges": "Fabrient manufacturing lifecycle tool: check sharp edges.",
    "check_small_features": "Fabrient manufacturing lifecycle tool: check small features.",
    "check_text_legibility": "Fabrient manufacturing lifecycle tool: check text legibility.",
    "check_embossed_features": "Fabrient manufacturing lifecycle tool: check embossed features.",
    "check_threads": "Fabrient manufacturing lifecycle tool: check threads.",
    "check_press_fits": "Fabrient manufacturing lifecycle tool: check press fits.",
    "check_snap_fits": "Fabrient manufacturing lifecycle tool: check snap fits.",
    "check_insert_pockets": "Fabrient manufacturing lifecycle tool: check insert pockets.",
    "check_connector_clearance": "Fabrient manufacturing lifecycle tool: check connector clearance.",
    "check_cable_clearance": "Fabrient manufacturing lifecycle tool: check cable clearance.",
    "check_pcb_clearance": "Fabrient manufacturing lifecycle tool: check pcb clearance.",
    "check_component_keepouts": "Fabrient manufacturing lifecycle tool: check component keepouts.",
    "check_revision_consistency": "Fabrient manufacturing lifecycle tool: check revision consistency.",
    "compare_revisions": "Fabrient manufacturing lifecycle tool: compare revisions.",
    "trace_provenance": "Fabrient manufacturing lifecycle tool: trace provenance.",
    "build_inspection_plan": "Fabrient manufacturing lifecycle tool: build inspection plan.",
    "map_inspection_columns": "Fabrient manufacturing lifecycle tool: map inspection columns.",
    "calibrate_from_observations": "Fabrient manufacturing lifecycle tool: calibrate from observations.",
    "estimate_risk": "Fabrient manufacturing lifecycle tool: estimate risk.",
    "calculate_reverification": "Fabrient manufacturing lifecycle tool: calculate reverification.",
    "propose_next_experiment": "Fabrient manufacturing lifecycle tool: propose next experiment.",
    "run_bounded_engineering_review": "Fabrient manufacturing lifecycle tool: run bounded engineering review.",
}

def _safe_name(name: str) -> str:
    return name.replace('-', '_')

async def _toolbox(name: str, payload: dict[str, Any]) -> Any:
    return await _request("POST", f"/v1/toolbox/{_safe_name(name)}", json={"operation": name, "payload": payload})

@mcp.tool(name="inspect_part", description=TOOL_DESCRIPTIONS["inspect_part"])
async def inspect_part(payload: dict[str, Any]) -> Any: return await _toolbox("inspect_part", payload)
@mcp.tool(name="analyze_dfm", description=TOOL_DESCRIPTIONS["analyze_dfm"])
async def analyze_dfm(payload: dict[str, Any]) -> Any: return await _toolbox("analyze_dfm", payload)
@mcp.tool(name="auto_fix_dfm", description=TOOL_DESCRIPTIONS["auto_fix_dfm"])
async def auto_fix_dfm(payload: dict[str, Any]) -> Any: return await _toolbox("auto_fix_dfm", payload)
@mcp.tool(name="verify_fixes", description=TOOL_DESCRIPTIONS["verify_fixes"])
async def verify_fixes(payload: dict[str, Any]) -> Any: return await _toolbox("verify_fixes", payload)
@mcp.tool(name="generate_manufacturing_package", description=TOOL_DESCRIPTIONS["generate_manufacturing_package"])
async def generate_manufacturing_package(payload: dict[str, Any]) -> Any: return await _toolbox("generate_manufacturing_package", payload)
@mcp.tool(name="generate_physical_build_guide", description=TOOL_DESCRIPTIONS["generate_physical_build_guide"])
async def generate_physical_build_guide(payload: dict[str, Any]) -> Any: return await _toolbox("generate_physical_build_guide", payload)
@mcp.tool(name="release_manufacturing_package", description=TOOL_DESCRIPTIONS["release_manufacturing_package"])
async def release_manufacturing_package(payload: dict[str, Any]) -> Any: return await _toolbox("release_manufacturing_package", payload)
@mcp.tool(name="validate_material", description=TOOL_DESCRIPTIONS["validate_material"])
async def validate_material(payload: dict[str, Any]) -> Any: return await _toolbox("validate_material", payload)
@mcp.tool(name="validate_machine_envelope", description=TOOL_DESCRIPTIONS["validate_machine_envelope"])
async def validate_machine_envelope(payload: dict[str, Any]) -> Any: return await _toolbox("validate_machine_envelope", payload)

# Remaining DFM checks intentionally remain thin, deterministic API adapters.
for _name in ["check_wall_thickness","check_clearances","check_holes","check_overhangs","check_bridges","check_supports","check_orientation","check_tolerances","check_fit","check_warp_risk","check_first_layer","check_thermal_risk","check_print_time","check_material_usage","check_bed_adhesion","check_part_split","check_fastener_access","check_assembly_order","check_service_access","check_draft","check_sharp_edges","check_small_features","check_text_legibility","check_embossed_features","check_threads","check_press_fits","check_snap_fits","check_insert_pockets","check_connector_clearance","check_cable_clearance","check_pcb_clearance","check_component_keepouts","check_revision_consistency","compare_revisions","trace_provenance","build_inspection_plan","map_inspection_columns"]:
    def _make_tool(name: str):
        async def _tool(payload: dict[str, Any]) -> Any: return await _toolbox(name, payload)
        _tool.__name__ = name
        return _tool
    mcp.tool(name=_name, description=TOOL_DESCRIPTIONS[_name])(_make_tool(_name))

@mcp.tool(name="calibrate_from_observations", description=TOOL_DESCRIPTIONS["calibrate_from_observations"])
async def calibrate_from_observations(payload: dict[str, Any]) -> Any: return await _request("POST", "/v1/calibrate", json=payload)
@mcp.tool(name="estimate_risk", description=TOOL_DESCRIPTIONS["estimate_risk"])
async def estimate_risk(payload: dict[str, Any]) -> Any: return await _request("POST", "/v1/uncertainty", json=payload)
@mcp.tool(name="calculate_reverification", description=TOOL_DESCRIPTIONS["calculate_reverification"])
async def calculate_reverification(payload: dict[str, Any]) -> Any: return await _request("POST", "/v1/reverification", json=payload)
@mcp.tool(name="propose_next_experiment", description=TOOL_DESCRIPTIONS["propose_next_experiment"])
async def propose_next_experiment(payload: dict[str, Any]) -> Any: return await _request("POST", "/v1/next-experiment", json=payload)
@mcp.tool(name="run_bounded_engineering_review", description=TOOL_DESCRIPTIONS["run_bounded_engineering_review"])
async def run_bounded_engineering_review(payload: dict[str, Any]) -> Any: return await _toolbox("run_bounded_engineering_review", payload)

if __name__ == "__main__": mcp.run(transport="streamable-http")

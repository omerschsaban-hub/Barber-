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
async def inspect_part(payload: dict[str, Any]) -> Any:
    return await _toolbox("inspect_part", payload)
@mcp.tool(name="analyze_dfm", description=TOOL_DESCRIPTIONS["analyze_dfm"])
async def analyze_dfm(payload: dict[str, Any]) -> Any:
    return await _toolbox("analyze_dfm", payload)
@mcp.tool(name="auto_fix_dfm", description=TOOL_DESCRIPTIONS["auto_fix_dfm"])
async def auto_fix_dfm(payload: dict[str, Any]) -> Any:
    return await _toolbox("auto_fix_dfm", payload)
@mcp.tool(name="verify_fixes", description=TOOL_DESCRIPTIONS["verify_fixes"])
async def verify_fixes(payload: dict[str, Any]) -> Any:
    return await _toolbox("verify_fixes", payload)
@mcp.tool(name="generate_manufacturing_package", description=TOOL_DESCRIPTIONS["generate_manufacturing_package"])
async def generate_manufacturing_package(payload: dict[str, Any]) -> Any:
    return await _toolbox("generate_manufacturing_package", payload)
@mcp.tool(name="release_manufacturing_package", description=TOOL_DESCRIPTIONS["release_manufacturing_package"])
async def release_manufacturing_package(payload: dict[str, Any]) -> Any:
    return await _toolbox("release_manufacturing_package", payload)
@mcp.tool(name="validate_material", description=TOOL_DESCRIPTIONS["validate_material"])
async def validate_material(payload: dict[str, Any]) -> Any:
    return await _toolbox("validate_material", payload)
@mcp.tool(name="validate_machine_envelope", description=TOOL_DESCRIPTIONS["validate_machine_envelope"])
async def validate_machine_envelope(payload: dict[str, Any]) -> Any:
    return await _toolbox("validate_machine_envelope", payload)
@mcp.tool(name="check_wall_thickness", description=TOOL_DESCRIPTIONS["check_wall_thickness"])
async def check_wall_thickness(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_wall_thickness", payload)
@mcp.tool(name="check_clearances", description=TOOL_DESCRIPTIONS["check_clearances"])
async def check_clearances(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_clearances", payload)
@mcp.tool(name="check_holes", description=TOOL_DESCRIPTIONS["check_holes"])
async def check_holes(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_holes", payload)
@mcp.tool(name="check_overhangs", description=TOOL_DESCRIPTIONS["check_overhangs"])
async def check_overhangs(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_overhangs", payload)
@mcp.tool(name="check_bridges", description=TOOL_DESCRIPTIONS["check_bridges"])
async def check_bridges(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_bridges", payload)
@mcp.tool(name="check_supports", description=TOOL_DESCRIPTIONS["check_supports"])
async def check_supports(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_supports", payload)
@mcp.tool(name="check_orientation", description=TOOL_DESCRIPTIONS["check_orientation"])
async def check_orientation(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_orientation", payload)
@mcp.tool(name="check_tolerances", description=TOOL_DESCRIPTIONS["check_tolerances"])
async def check_tolerances(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_tolerances", payload)
@mcp.tool(name="check_fit", description=TOOL_DESCRIPTIONS["check_fit"])
async def check_fit(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_fit", payload)
@mcp.tool(name="check_warp_risk", description=TOOL_DESCRIPTIONS["check_warp_risk"])
async def check_warp_risk(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_warp_risk", payload)
@mcp.tool(name="check_first_layer", description=TOOL_DESCRIPTIONS["check_first_layer"])
async def check_first_layer(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_first_layer", payload)
@mcp.tool(name="check_thermal_risk", description=TOOL_DESCRIPTIONS["check_thermal_risk"])
async def check_thermal_risk(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_thermal_risk", payload)
@mcp.tool(name="check_print_time", description=TOOL_DESCRIPTIONS["check_print_time"])
async def check_print_time(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_print_time", payload)
@mcp.tool(name="check_material_usage", description=TOOL_DESCRIPTIONS["check_material_usage"])
async def check_material_usage(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_material_usage", payload)
@mcp.tool(name="check_bed_adhesion", description=TOOL_DESCRIPTIONS["check_bed_adhesion"])
async def check_bed_adhesion(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_bed_adhesion", payload)
@mcp.tool(name="check_part_split", description=TOOL_DESCRIPTIONS["check_part_split"])
async def check_part_split(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_part_split", payload)
@mcp.tool(name="check_fastener_access", description=TOOL_DESCRIPTIONS["check_fastener_access"])
async def check_fastener_access(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_fastener_access", payload)
@mcp.tool(name="check_assembly_order", description=TOOL_DESCRIPTIONS["check_assembly_order"])
async def check_assembly_order(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_assembly_order", payload)
@mcp.tool(name="check_service_access", description=TOOL_DESCRIPTIONS["check_service_access"])
async def check_service_access(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_service_access", payload)
@mcp.tool(name="check_draft", description=TOOL_DESCRIPTIONS["check_draft"])
async def check_draft(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_draft", payload)
@mcp.tool(name="check_sharp_edges", description=TOOL_DESCRIPTIONS["check_sharp_edges"])
async def check_sharp_edges(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_sharp_edges", payload)
@mcp.tool(name="check_small_features", description=TOOL_DESCRIPTIONS["check_small_features"])
async def check_small_features(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_small_features", payload)
@mcp.tool(name="check_text_legibility", description=TOOL_DESCRIPTIONS["check_text_legibility"])
async def check_text_legibility(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_text_legibility", payload)
@mcp.tool(name="check_embossed_features", description=TOOL_DESCRIPTIONS["check_embossed_features"])
async def check_embossed_features(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_embossed_features", payload)
@mcp.tool(name="check_threads", description=TOOL_DESCRIPTIONS["check_threads"])
async def check_threads(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_threads", payload)
@mcp.tool(name="check_press_fits", description=TOOL_DESCRIPTIONS["check_press_fits"])
async def check_press_fits(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_press_fits", payload)
@mcp.tool(name="check_snap_fits", description=TOOL_DESCRIPTIONS["check_snap_fits"])
async def check_snap_fits(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_snap_fits", payload)
@mcp.tool(name="check_insert_pockets", description=TOOL_DESCRIPTIONS["check_insert_pockets"])
async def check_insert_pockets(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_insert_pockets", payload)
@mcp.tool(name="check_connector_clearance", description=TOOL_DESCRIPTIONS["check_connector_clearance"])
async def check_connector_clearance(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_connector_clearance", payload)
@mcp.tool(name="check_cable_clearance", description=TOOL_DESCRIPTIONS["check_cable_clearance"])
async def check_cable_clearance(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_cable_clearance", payload)
@mcp.tool(name="check_pcb_clearance", description=TOOL_DESCRIPTIONS["check_pcb_clearance"])
async def check_pcb_clearance(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_pcb_clearance", payload)
@mcp.tool(name="check_component_keepouts", description=TOOL_DESCRIPTIONS["check_component_keepouts"])
async def check_component_keepouts(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_component_keepouts", payload)
@mcp.tool(name="check_revision_consistency", description=TOOL_DESCRIPTIONS["check_revision_consistency"])
async def check_revision_consistency(payload: dict[str, Any]) -> Any:
    return await _toolbox("check_revision_consistency", payload)
@mcp.tool(name="compare_revisions", description=TOOL_DESCRIPTIONS["compare_revisions"])
async def compare_revisions(payload: dict[str, Any]) -> Any:
    return await _toolbox("compare_revisions", payload)
@mcp.tool(name="trace_provenance", description=TOOL_DESCRIPTIONS["trace_provenance"])
async def trace_provenance(payload: dict[str, Any]) -> Any:
    return await _toolbox("trace_provenance", payload)
@mcp.tool(name="build_inspection_plan", description=TOOL_DESCRIPTIONS["build_inspection_plan"])
async def build_inspection_plan(payload: dict[str, Any]) -> Any:
    return await _toolbox("build_inspection_plan", payload)
@mcp.tool(name="map_inspection_columns", description=TOOL_DESCRIPTIONS["map_inspection_columns"])
async def map_inspection_columns(payload: dict[str, Any]) -> Any:
    return await _toolbox("map_inspection_columns", payload)
@mcp.tool(name="calibrate_from_observations", description=TOOL_DESCRIPTIONS["calibrate_from_observations"])
async def calibrate_from_observations(payload: dict[str, Any]) -> Any:
    return await _request("POST", "/v1/calibrate", json=payload)
@mcp.tool(name="estimate_risk", description=TOOL_DESCRIPTIONS["estimate_risk"])
async def estimate_risk(payload: dict[str, Any]) -> Any:
    return await _request("POST", "/v1/uncertainty", json=payload)
@mcp.tool(name="calculate_reverification", description=TOOL_DESCRIPTIONS["calculate_reverification"])
async def calculate_reverification(payload: dict[str, Any]) -> Any:
    return await _request("POST", "/v1/reverification", json=payload)
@mcp.tool(name="propose_next_experiment", description=TOOL_DESCRIPTIONS["propose_next_experiment"])
async def propose_next_experiment(payload: dict[str, Any]) -> Any:
    return await _request("POST", "/v1/next-experiment", json=payload)
@mcp.tool(name="run_bounded_engineering_review", description=TOOL_DESCRIPTIONS["run_bounded_engineering_review"])
async def run_bounded_engineering_review(payload: dict[str, Any]) -> Any:
    return await _toolbox("run_bounded_engineering_review", payload)

if __name__ == "__main__": mcp.run(transport="streamable-http")

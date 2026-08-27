from __future__ import annotations

import asyncio
import base64
import os

from mcp import ClientSession
try:
    from mcp.client.streamable_http import streamable_http_client
except ImportError:
    from mcp.client.streamable_http import streamablehttp_client as streamable_http_client

from server import CAPABILITY_NAMES

PNG_1X1 = base64.b64encode(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000000020001e221bc330000000049454e44ae426082")).decode()
STEP_MINIMAL = base64.b64encode(b"ISO-10303-21;HEADER;ENDSEC;DATA;ENDSEC;END-ISO-10303-21;").decode()

CHECK_FIXTURES = {
    "check_wall_thickness": {"wall_thickness_mm": 2.0, "minimum_wall_thickness_mm": 1.0},
    "check_clearances": {"clearance_mm": 1.0, "minimum_clearance_mm": 0.5},
    "check_holes": {"hole_diameter_mm": 3.0, "minimum_hole_diameter_mm": 2.0},
    "check_overhangs": {"overhang_angle_deg": 30.0, "maximum_overhang_angle_deg": 45.0},
    "check_bridges": {"bridge_length_mm": 5.0, "maximum_bridge_length_mm": 10.0},
    "check_tolerances": {"measured_mm": 10.0, "tolerance_mm": 0.2},
    "check_fit": {"measured_mm": 10.0, "target_mm": 9.8},
}

def fixture(name: str) -> dict:
    if name == "validate_dimension":
        return {"nominal_mm": 10.0, "measured_mm": 10.0, "tolerance_mm": 0.1}
    if name in CHECK_FIXTURES:
        return CHECK_FIXTURES[name]
    if name in {"physics_predict"}:
        return {"nominal_mm": 10.0, "material": "PETG", "machine": "test-machine", "process": "FDM"}
    if name in {"calibration_fit", "calibrate_from_observations", "system_identification", "final_system_identification", "residual_uncertainty", "ml_machine_system_id", "ml_data_quality", "ml_training_data_audit"}:
        return {"observations": [{"predicted_mm": 10.0 + i, "measured_mm": 10.01 + i, "context": {"machine": "test-machine"}} for i in range(10)]}
    if name == "simulation_run":
        return {"nominal_mm": 10.0, "samples": 10, "seed": 42}
    if name in {"cad_step_extract", "inspect_part", "analyze_dfm", "dfm_analyze", "cad_manufacturing_risk", "cad_wall_clearance_review", "cad_hole_review", "cad_overhang_review", "cad_bridge_review", "cad_tolerance_review"}:
        return {"filename": "contract.step", "file_base64": STEP_MINIMAL}
    if name in {"cv_measure", "cv_measure_real", "cv_measure_real_json", "cv_detect_line_candidates"}:
        return {"filename": "contract.png", "file_base64": PNG_1X1, "image_base64": PNG_1X1, "reference_length_mm": 10.0, "reference_pixel_span": 10.0}
    if name == "inspection_confirm":
        return {"confirm": True, "record_ids": []}
    if name in {"acceptance_gate", "deterministic_acceptance"}:
        return {"physical_evidence": [{"id": "fixture-1", "status": "observed"}]}
    if name == "validate_material":
        return {"material": "PETG"}
    if name == "validate_machine_envelope":
        return {"machine_envelope": {"x_mm": 220, "y_mm": 220, "z_mm": 250}}
    if name in {"trace_provenance", "manufacturing_provenance"}:
        return {"provenance": {"source": "fixture", "synthetic": False}}
    if name == "risk_map":
        return {"findings": [{"id": "fixture-risk", "risk_score": 0.2, "category": "fixture", "message": "contract test"}]}
    if name in {"risk_estimate", "final_system_identification", "agent_graph", "agent_step", "engineering_agent_run", "run_bounded_engineering_review", "agent_fleet_run", "llm_engineering_critic", "next_experiment", "propose_next_experiment", "calculate_reverification", "reverification_calculate", "uncertainty_calculate", "sim2real_run", "sim2real_compare", "sim2real_calibrate_and_run"}:
        return {"observations": [{"predicted_mm": 10.0 + i, "measured_mm": 10.01 + i} for i in range(10)], "seed": 42}
    return {"contract_test": True, "fixture": name, "evidence": {"source": "caller", "synthetic": False}}

async def main() -> None:
    url = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
    token = os.getenv("FABRIENT_MCP_AUTH_TOKEN", "").strip()
    headers = {"Authorization": f"Bearer {token}"} if token else None
    async with streamable_http_client(url, headers=headers) as streams:
        read_stream, write_stream = streams[:2]
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = [tool.name for tool in listed.tools]
            assert names == CAPABILITY_NAMES, "tools/list does not match the authoritative registry"
            assert len(names) == 100 and len(set(names)) == 100
            failures: list[str] = []
            for name in CAPABILITY_NAMES:
                try:
                    arguments = fixture(name)
                    if name == "validate_dimension":
                        result = await asyncio.wait_for(session.call_tool(name, arguments=arguments), timeout=30)
                    else:
                        result = await asyncio.wait_for(session.call_tool(name, arguments={"payload": arguments}), timeout=30)
                    if not result.content:
                        failures.append(f"{name}: empty result")
                        continue
                    rendered = " ".join(getattr(block, "text", "") or "" for block in result.content)
                    if "unsupported_operation" in rendered.lower():
                        failures.append(f"{name}: unsupported_operation response")
                except Exception as exc:
                    failures.append(f"{name}: {exc}")
            if failures:
                raise AssertionError("MCP tools/call failures:\n" + "\n".join(failures))
            print(f"MCP contract smoke OK: tools/list={len(names)}, tools/call={len(CAPABILITY_NAMES)}, failures=0")

if __name__ == "__main__":
    asyncio.run(main())

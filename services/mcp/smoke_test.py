from __future__ import annotations

import asyncio
import base64
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from server import CAPABILITY_NAMES

# Tiny deterministic fixtures. They are only for transport/contract validation;
# they are never treated as engineering evidence.
PNG_1X1 = base64.b64encode(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000000020001e221bc330000000049454e44ae426082")).decode()
STEP_MINIMAL = base64.b64encode(b"ISO-10303-21;HEADER;ENDSEC;DATA;ENDSEC;END-ISO-10303-21;").decode()


def fixture(name: str) -> dict:
    if name == "validate_dimension":
        return {"nominal_mm": 10.0, "measured_mm": 10.0, "tolerance_mm": 0.1}
    if name == "physics_predict":
        return {"nominal_mm": 10.0, "material": "PETG", "machine": "test-machine", "process": "FDM"}
    if name == "calibration_fit":
        return {"observations": [{"predicted_mm": 10.0 + i, "measured_mm": 10.01 + i} for i in range(10)]}
    if name in {"simulation_run"}:
        return {"nominal_mm": 10.0, "samples": 10}
    if name in {"cad_step_extract"}:
        return {"filename": "contract.step", "file_base64": STEP_MINIMAL}
    if name in {"cv_measure", "cv_measure_real", "cv_measure_real_json", "cv_detect_line_candidates"}:
        return {"filename": "contract.png", "file_base64": PNG_1X1, "image_base64": PNG_1X1, "reference_length_mm": 10.0, "reference_pixel_span": 10.0}
    if name == "inspection_confirm":
        return {"confirm": True}
    if name == "acceptance_gate":
        return {"physical_evidence": []}
    return {}


async def main() -> None:
    url = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
    async with streamable_http_client(url) as (read_stream, write_stream, _):
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
                        result = await session.call_tool(name, arguments=arguments)
                    else:
                        result = await session.call_tool(name, arguments={"payload": arguments})
                    if not result.content:
                        failures.append(f"{name}: empty result")
                    # A missing-input/evidence gate is valid. A transport exception,
                    # empty result, or server error is not. The MCP server must not
                    # manufacture a passing engineering result merely to satisfy smoke.
                except Exception as exc:
                    failures.append(f"{name}: {exc}")

            if failures:
                raise AssertionError("MCP tools/call failures:\n" + "\n".join(failures))
            print(f"MCP contract smoke OK: tools/list={len(names)}, tools/call={len(CAPABILITY_NAMES)}")


if __name__ == "__main__":
    asyncio.run(main())

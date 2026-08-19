from __future__ import annotations
import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

ENGINEERING_API = os.getenv("FABRIENT_ENGINEERING_API", "http://localhost:8000").rstrip("/")
mcp = FastMCP("Fabrient Engineering")

async def _request(method: str, path: str, *, json: Any = None, files: Any = None, timeout: float = 60.0) -> Any:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.request(method, f"{ENGINEERING_API}{path}", json=json, files=files)
        try: data = r.json()
        except Exception: data = {"text": r.text}
        if r.status_code >= 400: raise RuntimeError(f"Engineering API {r.status_code}: {data}")
        return data

def _tool(name: str, description: str, path: str, method: str = "POST"):
    async def call(payload: dict[str, Any]) -> dict[str, Any]:
        return await _request(method, path, json=payload)
    call.__name__ = name
    call.__doc__ = description
    mcp.tool(name=name, description=description)(call)

_tool("predict_dimension", "Deterministic physics prediction with 95% interval and provenance.", "/v1/predict")
_tool("simulate_process", "Run seeded domain-randomized simulation and return uncertainty summary/provenance.", "/v1/simulate")
_tool("calibrate_machine", "Fit residual calibration from real observations with held-out validation.", "/v1/calibrate")
_tool("estimate_uncertainty", "Combine physics, measurement, and model uncertainty without inventing evidence.", "/v1/uncertainty")
_tool("check_acceptance", "Apply explicit acceptance/refusal gates to measured variation and uncertainty.", "/v1/acceptance")
_tool("calculate_reverification", "Calculate a bounded re-verification interval from observed drift, wear, uncertainty, usage, environment and consequence severity.", "/v1/reverification")
_tool("propose_next_experiment", "Select an information-gaining experiment from measured uncertainty; physical execution remains human-gated.", "/v1/next-experiment")

@mcp.tool(name="health", description="Check the Fabrient engineering API health and version.")
async def health() -> dict[str, Any]:
    return await _request("GET", "/health")

@mcp.tool(name="capabilities", description="Return the MCP's exposed engineering capability map and safety guarantees.")
async def capabilities() -> dict[str, Any]:
    return {"service":"fabrient-engineering","transport":"streamable-http","capabilities":["deterministic_physics","simulation_domain_randomization","real_observation_calibration","uncertainty","acceptance_refusal","reverification","next_experiment","inspection_ingestion","step_geometry","computer_vision","machine_system_identification","residual_ml","provenance","audit_reports","bounded_agent_orchestration"],"guarantees":["no synthetic observations used for calibration","provenance returned by engineering endpoints","acceptance can refuse unsupported claims","physical/external actions require human approval"]}

@mcp.tool(name="preview_inspection_csv", description="Preview an uploaded inspection CSV and return deterministic column mapping suggestions. Pass UTF-8 CSV text.")
async def preview_inspection_csv(filename: str, csv_text: str) -> dict[str, Any]:
    return await _request("POST", "/v1/import/preview", files={"file":(filename,csv_text.encode("utf-8"),"text/csv")})

@mcp.tool(name="extract_step_geometry", description="Extract supported STEP geometry evidence and a bounded bounding box. Unsupported topology or units are reported rather than invented.")
async def extract_step_geometry(filename: str, step_text: str) -> dict[str, Any]:
    return await _request("POST", "/v1/geometry/step", files={"file":(filename,step_text.encode("utf-8"),"application/step")})

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

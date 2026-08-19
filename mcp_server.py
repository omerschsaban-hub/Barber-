from __future__ import annotations
import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

ENGINEERING_API = os.getenv("FABRIENT_ENGINEERING_API", "http://localhost:8000").rstrip("/")
mcp = FastMCP("Fabrient Engineering")

async def _request(method: str, path: str, *, json: Any = None, files: Any = None, params: Any = None, timeout: float = 120.0) -> Any:
    if not path.startswith("/") or path.startswith("//") or not path.startswith("/v1/") and path != "/health" and path != "/openapi.json":
        raise ValueError("Only Fabrient engineering API paths are permitted")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.request(method.upper(), f"{ENGINEERING_API}{path}", json=json, files=files, params=params)
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

# Core typed engineering tools.
_tool("predict_dimension", "Deterministic physics prediction with 95% interval and provenance.", "/v1/predict")
_tool("simulate_process", "Run seeded domain-randomized simulation and return uncertainty summary/provenance.", "/v1/simulate")
_tool("calibrate_machine", "Fit residual calibration from real observations with held-out validation.", "/v1/calibrate")
_tool("estimate_uncertainty", "Combine physics, measurement, and model uncertainty without inventing evidence.", "/v1/uncertainty")
_tool("check_acceptance", "Apply explicit acceptance/refusal gates to measured variation and uncertainty.", "/v1/acceptance")
_tool("calculate_reverification", "Calculate a bounded re-verification interval from observed drift, wear, uncertainty, usage, environment and consequence severity.", "/v1/reverification")
_tool("propose_next_experiment", "Select an information-gaining experiment from measured uncertainty; physical execution remains human-gated.", "/v1/next-experiment")

@mcp.tool(name="health", description="Check Fabrient engineering API health and version.")
async def health() -> dict[str, Any]: return await _request("GET", "/health")

@mcp.tool(name="api_openapi", description="Return the live engineering API OpenAPI schema. This is the authoritative discovery surface for every exposed endpoint.")
async def api_openapi() -> dict[str, Any]: return await _request("GET", "/openapi.json")

@mcp.tool(name="list_engineering_capabilities", description="Discover every live Fabrient API route, HTTP method, summary, description, parameters and request schema from the live OpenAPI contract.")
async def list_engineering_capabilities() -> dict[str, Any]:
    spec = await _request("GET", "/openapi.json")
    routes=[]
    for path, methods in spec.get("paths", {}).items():
        for method, operation in methods.items():
            if method.lower() in {"get","post","put","patch","delete"}:
                routes.append({"path":path,"method":method.upper(),"operation_id":operation.get("operationId"),"summary":operation.get("summary"),"description":operation.get("description"),"parameters":operation.get("parameters",[]),"request_body":operation.get("requestBody")})
    return {"service":spec.get("info",{}),"route_count":len(routes),"routes":routes}

@mcp.tool(name="invoke_engineering_api", description="Universal Fabrient engineering gateway. Invoke any currently exposed /v1/* or /health endpoint using its exact OpenAPI path and HTTP method. Use list_engineering_capabilities first for discovery. This prevents the MCP from becoming stale when new engineering capabilities are added.")
async def invoke_engineering_api(method: str, path: str, payload: dict[str, Any] | None = None, query: dict[str, Any] | None = None) -> Any:
    return await _request(method, path, json=payload, params=query)

@mcp.tool(name="capabilities", description="Return the MCP architecture, guarantees and broad Fabrient capability domains.")
async def capabilities() -> dict[str, Any]:
    return {"service":"fabrient-engineering","transport":"streamable-http","coverage":"live OpenAPI + universal /v1 gateway","domains":["deterministic physics","simulation/domain randomization","real observation calibration","uncertainty","acceptance/refusal","re-verification","next experiment","inspection ingestion","STEP geometry","computer vision","machine/process identification","residual ML","provenance/audit","bounded engineering orchestration"],"guarantees":["calibration uses real observations only","engineering responses retain provenance where implemented","unsupported acceptance claims can be refused","no physical/external action is executed by this MCP gateway"]}

@mcp.tool(name="preview_inspection_csv", description="Preview an uploaded inspection CSV and return deterministic column mapping suggestions. Pass UTF-8 CSV text.")
async def preview_inspection_csv(filename: str, csv_text: str) -> dict[str, Any]:
    return await _request("POST", "/v1/import/preview", files={"file":(filename,csv_text.encode("utf-8"),"text/csv")})

@mcp.tool(name="extract_step_geometry", description="Extract supported STEP geometry evidence and a bounded bounding box. Unsupported topology or units are reported rather than invented.")
async def extract_step_geometry(filename: str, step_text: str) -> dict[str, Any]:
    return await _request("POST", "/v1/geometry/step", files={"file":(filename,step_text.encode("utf-8"),"application/step")})

if __name__ == "__main__": mcp.run(transport="streamable-http")

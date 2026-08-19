from __future__ import annotations
import os
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

ENGINEERING_API = os.getenv("FABRIENT_ENGINEERING_API", "http://localhost:8000").rstrip("/")
MCP_AUTH_TOKEN = os.getenv("FABRIENT_MCP_AUTH_TOKEN", "").strip()
mcp = FastMCP("Fabrient Engineering")

async def _request(method: str, path: str, *, json: Any = None, files: Any = None, params: Any = None, timeout: float = 120.0) -> Any:
    if not path.startswith("/") or path.startswith("//") or (not path.startswith("/v1/") and path not in {"/health", "/openapi.json"}):
        raise ValueError("Only Fabrient engineering API paths are permitted")
    headers = {"Authorization": f"Bearer {MCP_AUTH_TOKEN}"} if MCP_AUTH_TOKEN else {}
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.request(method.upper(), f"{ENGINEERING_API}{path}", json=json, files=files, params=params, headers=headers)
        try: data = r.json()
        except Exception: data = {"text": r.text}
        if r.status_code >= 400: raise RuntimeError(f"Engineering API {r.status_code}: {data}")
        return data

TOOL_DESCRIPTIONS={"generate_manufacturing_package":"Generate a verified Fabrient manufacturing package.","generate_physical_build_guide":"Generate a simple step-by-step physical build guide.","release_manufacturing_package":"Release a manufacturing package only after required gates pass.","inspect_part":"Inspect a part.","analyze_dfm":"Analyze deterministic DFM constraints.","auto_fix_dfm":"Apply allowed deterministic DFM fixes.","verify_fixes":"Re-run verification after fixes."}
async def _toolbox(name:str,payload:dict[str,Any])->Any:return await _request("POST",f"/v1/toolbox/{name}",json={"operation":name,"payload":payload})

for _name in TOOL_DESCRIPTIONS:
    def _make_tool(name:str):
        async def _tool(payload:dict[str,Any])->Any:return await _toolbox(name,payload)
        _tool.__name__=name
        return _tool
    mcp.tool(name=_name,description=TOOL_DESCRIPTIONS[_name])(_make_tool(_name))

if __name__=="__main__":mcp.run(transport="streamable-http")

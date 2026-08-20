"""Provider-neutral gateway for verified official remote MCP integrations only."""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .mcp_integrations import MCP_PROVIDERS, public_provider_catalog, search_mcp_providers, provider_tool_help

_runtime_connections: dict[str, dict[str, str]] = {}

class IntegrationRequest(BaseModel):
    provider: str = Field(min_length=1)
    method: str = Field(default="tools/list", min_length=1)
    params: Dict[str, Any] = Field(default_factory=dict)

class ConnectionRequest(BaseModel):
    provider: str = Field(min_length=1)
    bearer_token: str | None = None

class MCPClient:
    def __init__(self, provider: str, token: str | None = None):
        config = MCP_PROVIDERS.get(provider)
        if not config:
            raise KeyError(provider)
        runtime = _runtime_connections.get(provider, {})
        self.provider = provider
        self.endpoint = config["endpoint"]
        self.token = token if token is not None else (runtime.get("token") or os.getenv(f"FABRIENT_{provider.upper()}_MCP_TOKEN", ""))

    @property
    def configured(self) -> bool:
        return self.provider == "autodesk_product_help" or bool(self.token)

    async def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
            response = await client.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError("MCP provider returned a non-object response")
        if "error" in body:
            raise RuntimeError(str(body["error"]))
        return body

def public_catalog() -> list[dict[str, Any]]:
    return [{**p, "configured": MCPClient(pid).configured} for pid, p in ((x["id"], x) for x in public_provider_catalog())]

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.get("/providers")
async def providers() -> Dict[str, Any]:
    return {"providers": public_catalog()}

@router.get("/search")
async def search(query: str = "", limit: int = 10) -> Dict[str, Any]:
    return {"query": query, "results": search_mcp_providers(query, min(max(limit, 1), 25))}

@router.get("/search-tools")
async def search_tools(query: str = "", limit: int = 20) -> Dict[str, Any]:
    terms = [t.lower() for t in query.split() if t.strip()]
    matches = []
    for provider in list(_runtime_connections):
        try:
            tools = (await MCPClient(provider).call("tools/list", {})).get("result", {}).get("tools", [])
        except Exception:
            continue
        for tool in tools:
            text = f"{tool.get('name','')} {tool.get('description','')}".lower()
            if not terms or all(t in text for t in terms):
                matches.append({"provider": provider, **tool})
    return {"query": query, "count": len(matches[:limit]), "tools": matches[:limit]}

@router.get("/provider/{provider}/help")
async def provider_help(provider: str) -> Dict[str, Any]:
    try:
        return provider_tool_help(provider)
    except KeyError:
        raise HTTPException(status_code=404, detail="Provider is not in the verified official MCP catalog")

@router.post("/auth/start")
async def auth_start(request: dict[str, str]) -> Dict[str, Any]:
    provider = request.get("provider", "")
    try:
        p = MCP_PROVIDERS[provider]
    except KeyError:
        raise HTTPException(status_code=404, detail="Provider is not in the verified official MCP catalog")
    if p["auth"] == "public":
        return {"provider": provider, "mode": "public", "auth_url": p["endpoint"], "mcp_url": p["endpoint"], "docs": p["docs"], "message": "No sign-in is required."}
    return {"provider": provider, "mode": "provider_oauth", "mcp_url": p["endpoint"], "docs": p["docs"], "message": "Use the provider's official MCP OAuth flow. Fabrient does not invent OAuth URLs or credentials."}

@router.post("/connect")
async def connect(request: ConnectionRequest) -> Dict[str, Any]:
    try:
        client = MCPClient(request.provider, request.bearer_token)
    except KeyError:
        raise HTTPException(status_code=404, detail="Provider is not in the verified official MCP catalog")
    if not client.configured:
        raise HTTPException(status_code=401, detail="Provider authorization is required")
    try:
        result = await client.call("tools/list", {})
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=f"Connection test failed: {exc}")
    if request.provider != "autodesk_product_help":
        _runtime_connections[request.provider] = {"token": request.bearer_token or ""}
    tools = result.get("result", {}).get("tools", [])
    return {"connected": True, "provider": request.provider, "endpoint": client.endpoint, "tool_count": len(tools), "tools": tools}

@router.post("/disconnect")
async def disconnect(request: dict[str, str]) -> Dict[str, Any]:
    provider = request.get("provider", "")
    _runtime_connections.pop(provider, None)
    return {"disconnected": True, "provider": provider}

@router.get("/connections")
async def connections() -> Dict[str, Any]:
    return {"connections": [{"provider": pid, "connected": bool(conn.get("token")), "tool_count": 0} for pid, conn in _runtime_connections.items()]}

@router.post("/discover-tools")
async def discover_tools(request: dict[str, str]) -> Dict[str, Any]:
    provider = request.get("provider", "")
    try:
        client = MCPClient(provider)
    except KeyError:
        raise HTTPException(status_code=404, detail="Provider is not in the verified official MCP catalog")
    if not client.configured:
        raise HTTPException(status_code=401, detail="Provider authorization is required")
    try:
        result = await client.call("tools/list", {})
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    tools = result.get("result", {}).get("tools", [])
    return {"provider": provider, "endpoint": client.endpoint, "tools": tools, "count": len(tools)}

@router.post("/mcp/call")
async def mcp_call(request: IntegrationRequest) -> Dict[str, Any]:
    try:
        client = MCPClient(request.provider)
    except KeyError:
        raise HTTPException(status_code=404, detail="Provider is not in the verified official MCP catalog")
    if not client.configured:
        raise HTTPException(status_code=401, detail="Provider authorization is required")
    try:
        return await client.call(request.method, request.params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Provider HTTP error: {exc.response.status_code}")
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))

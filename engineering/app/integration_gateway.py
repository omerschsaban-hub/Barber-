"""Provider-neutral gateway for authorized engineering-system integrations."""
from __future__ import annotations
import os
from typing import Any, Dict, Optional
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .mcp_integrations import MCP_PROVIDERS, public_provider_catalog, search_mcp_providers, provider_tool_help

# Existing provider credentials remain process-local for now; never return secrets.
_runtime_connections: dict[str, dict[str, str]] = {}

class IntegrationRequest(BaseModel):
    provider: str = Field(min_length=1)
    method: str = Field(default="tools/list", min_length=1)
    params: Dict[str, Any] = Field(default_factory=dict)

class ConnectionRequest(BaseModel):
    provider: str = Field(min_length=1)
    endpoint: str = Field(min_length=8)
    bearer_token: str | None = None

class MCPClient:
    def __init__(self, provider: str, endpoint: str | None = None, token: str | None = None):
        config = MCP_PROVIDERS.get(provider)
        if not config:
            raise KeyError(provider)
        runtime = _runtime_connections.get(provider, {})
        self.provider = provider
        self.endpoint = (endpoint or runtime.get("endpoint") or config.get("endpoint") or os.getenv(f"FABRIENT_{provider.upper()}_MCP_URL", "")).strip()
        self.token = token if token is not None else (runtime.get("token") or os.getenv(f"FABRIENT_{provider.upper()}_MCP_TOKEN", ""))

    @property
    def configured(self) -> bool:
        return bool(self.endpoint)

    async def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.endpoint:
            raise RuntimeError(f"{self.provider} is not configured")
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

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.get("/providers")
async def providers() -> Dict[str, Any]:
    return {"providers": [{**p, "configured": MCPClient(pid).configured} for pid, p in ((x["id"], x) for x in public_provider_catalog())]}

@router.get("/search")
async def search(query: str = "", limit: int = 10) -> Dict[str, Any]:
    return {"query": query, "results": search_mcp_providers(query, min(max(limit, 1), 25))}

@router.get("/provider/{provider}/help")
async def provider_help(provider: str) -> Dict[str, Any]:
    try:
        return provider_tool_help(provider)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown integration provider")

@router.post("/auth/start")
async def auth_start(request: dict[str, str]) -> Dict[str, Any]:
    provider = request.get("provider", "")
    p = MCP_PROVIDERS.get(provider)
    if not p:
        raise HTTPException(status_code=404, detail="Unknown integration provider")
    if p.get("auth") == "public":
        return {"provider": provider, "mode": "public", "auth_url": p.get("endpoint"), "message": "No sign-in is required."}
    if p.get("auth") == "local":
        return {"provider": provider, "mode": "local", "endpoint": p.get("endpoint"), "docs": p.get("docs"), "message": "Start the provider's local MCP server, then connect to the local endpoint."}
    endpoint = p.get("endpoint") or os.getenv(f"FABRIENT_{provider.upper()}_MCP_URL", "")
    if endpoint:
        return {"provider": provider, "mode": "oauth_discovery", "mcp_url": endpoint, "message": "Use MCP OAuth discovery against the provider endpoint; do not paste a token into the UI."}
    return {"provider": provider, "mode": "provider_auth", "docs": p.get("docs"), "message": "Provider authorization is required. Fabrient will use the provider's official authorization flow when an MCP endpoint is configured."}

@router.post("/connect")
async def connect(request: ConnectionRequest) -> Dict[str, Any]:
    if request.provider not in MCP_PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown integration provider")
    if not request.endpoint.startswith(("https://", "http://")):
        raise HTTPException(status_code=400, detail="MCP endpoint must use HTTP(S)")
    client = MCPClient(request.provider, request.endpoint, request.bearer_token)
    try:
        result = await client.call("tools/list", {})
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=f"Connection test failed: {exc}")
    _runtime_connections[request.provider] = {"endpoint": request.endpoint, "token": request.bearer_token or ""}
    tools = result.get("result", {}).get("tools", [])
    return {"connected": True, "provider": request.provider, "tool_count": len(tools), "tools": tools}

@router.post("/disconnect")
async def disconnect(request: dict[str, str]) -> Dict[str, Any]:
    provider = request.get("provider", "")
    if provider not in MCP_PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown integration provider")
    _runtime_connections.pop(provider, None)
    return {"disconnected": True, "provider": provider}

@router.get("/connections")
async def connections() -> Dict[str, Any]:
    return {"connections": [{"provider": pid, "connected": bool(conn.get("endpoint")), "tool_count": 0} for pid, conn in _runtime_connections.items()]}

@router.post("/discover-tools")
async def discover_tools(request: dict[str, str]) -> Dict[str, Any]:
    provider = request.get("provider", "")
    try:
        result = await MCPClient(provider).call("tools/list", {})
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown integration provider")
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    tools = result.get("result", {}).get("tools", [])
    return {"provider": provider, "tools": tools, "count": len(tools)}

@router.post("/mcp/call")
async def mcp_call(request: IntegrationRequest) -> Dict[str, Any]:
    try:
        return await MCPClient(request.provider).call(request.method, request.params)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown integration provider")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Provider HTTP error: {exc.response.status_code}")
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))

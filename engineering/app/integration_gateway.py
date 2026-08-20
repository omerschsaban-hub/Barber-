"""Provider-neutral gateway for authorized engineering-system integrations."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

@dataclass(frozen=True)
class ProviderConfig:
    key: str
    name: str
    transport: str
    endpoint_env: str
    token_env: str

PROVIDERS = {
    "autodesk_fusion": ProviderConfig("autodesk_fusion", "Autodesk Fusion MCP", "mcp", "FABRIENT_FUSION_MCP_URL", "FABRIENT_FUSION_MCP_TOKEN"),
    "propel_plm": ProviderConfig("propel_plm", "Propel PLM MCP", "mcp", "FABRIENT_PROPEL_MCP_URL", "FABRIENT_PROPEL_MCP_TOKEN"),
}

# Runtime connection registry. Secrets are held only in process memory and are
# never returned by API responses. Production deployments can replace this
# with the authenticated secret store without changing the public contract.
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
    def __init__(self, config: ProviderConfig, endpoint: str | None = None, token: str | None = None):
        self.config = config
        runtime = _runtime_connections.get(config.key, {})
        self.endpoint = (endpoint or runtime.get("endpoint") or os.getenv(config.endpoint_env, "")).strip()
        self.token = token if token is not None else (runtime.get("token") or os.getenv(config.token_env, ""))

    @property
    def configured(self) -> bool:
        return bool(self.endpoint)

    async def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.endpoint:
            raise RuntimeError(f"{self.config.key} is not configured")
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

def client_for(provider: str) -> MCPClient:
    config = PROVIDERS.get(provider)
    if not config:
        raise KeyError(provider)
    return MCPClient(config)

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.get("/providers")
async def providers() -> Dict[str, Any]:
    return {"providers": [{"key": c.key, "name": c.name, "transport": c.transport, "configured": client_for(c.key).configured} for c in PROVIDERS.values()]}

@router.post("/connect")
async def connect(request: ConnectionRequest) -> Dict[str, Any]:
    if request.provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown integration provider")
    if not request.endpoint.startswith(("https://", "http://")):
        raise HTTPException(status_code=400, detail="MCP endpoint must use HTTP(S)")
    client = MCPClient(PROVIDERS[request.provider], request.endpoint, request.bearer_token)
    try:
        result = await client.call("tools/list", {})
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=f"Connection test failed: {exc}")
    _runtime_connections[request.provider] = {"endpoint": request.endpoint, "token": request.bearer_token or ""}
    return {"connected": True, "provider": request.provider, "tool_count": len(result.get("result", {}).get("tools", []))}

@router.post("/disconnect")
async def disconnect(request: dict[str, str]) -> Dict[str, Any]:
    provider = request.get("provider", "")
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown integration provider")
    _runtime_connections.pop(provider, None)
    return {"disconnected": True, "provider": provider}

@router.post("/mcp/call")
async def mcp_call(request: IntegrationRequest) -> Dict[str, Any]:
    try:
        client = client_for(request.provider)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown integration provider")
    try:
        return await client.call(request.method, request.params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Provider HTTP error: {exc.response.status_code}")
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))

async def inspect_provider(provider: str) -> Dict[str, Any]:
    client = client_for(provider)
    if not client.configured:
        return {"provider": provider, "configured": False, "tools": []}
    result = await client.call("tools/list", {})
    return {"provider": provider, "configured": True, "result": result}

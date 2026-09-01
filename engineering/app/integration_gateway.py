"""Provider-neutral gateway for official remote MCP integrations.

The gateway owns the user's external integration connection. OAuth is PKCE-based,
tokens are encrypted at rest, and the same connection is consumed by the web app
and authenticated MCP requests.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .auth_db import user_from_bearer
from .integration_oauth import complete as oauth_complete
from .integration_oauth import connection_token, start as oauth_start
from .mcp_integrations import MCP_PROVIDERS, public_provider_catalog, search_mcp_providers, provider_tool_help
from .product_intelligence import record

_runtime_connections: dict[str, dict[str, str]] = {}


class IntegrationRequest(BaseModel):
    provider: str = Field(min_length=1)
    method: str = Field(default="tools/list", min_length=1)
    params: Dict[str, Any] = Field(default_factory=dict)
    project_id: str | None = None
    entity_id: str | None = None


class ConnectionRequest(BaseModel):
    provider: str = Field(min_length=1)
    bearer_token: str | None = None


class OAuthCompleteRequest(BaseModel):
    code: str = Field(min_length=1)
    state: str = Field(min_length=1)


def _identity(authorization: str | None) -> dict[str, Any] | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return user_from_bearer(authorization[7:].strip())


class MCPClient:
    def __init__(self, provider: str, token: str | None = None, user_id: str | None = None):
        config = MCP_PROVIDERS.get(provider)
        if not config:
            raise KeyError(provider)
        self.provider = provider
        self.endpoint = config["endpoint"]
        stored = connection_token(user_id, provider) if user_id else None
        self.token = token or stored or _runtime_connections.get(provider, {}).get("token") or os.getenv(f"FABRIENT_{provider.upper()}_MCP_TOKEN", "")

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


router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/providers")
async def providers() -> Dict[str, Any]:
    return {"providers": public_provider_catalog()}


@router.get("/search")
async def search(query: str = "", limit: int = 10) -> Dict[str, Any]:
    return {"query": query, "results": search_mcp_providers(query, min(max(limit, 1), 25))}


@router.get("/search-tools")
async def search_tools(query: str = "", limit: int = 20, authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    identity = _identity(authorization)
    terms = [t.lower() for t in query.split() if t.strip()]
    matches = []
    providers_to_search = list(_runtime_connections)
    if identity:
        from .integration_oauth import connection_providers
        providers_to_search = list(set(providers_to_search) | set(connection_providers(identity["user_id"])))
    for provider in providers_to_search:
        try:
            tools = (await MCPClient(provider, user_id=identity["user_id"] if identity else None).call("tools/list", {})).get("result", {}).get("tools", [])
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
async def auth_start(request: dict[str, str], authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    return oauth_start(request.get("provider", ""), authorization)


@router.post("/auth/complete")
async def auth_complete(request: OAuthCompleteRequest) -> Dict[str, Any]:
    return oauth_complete(request.code, request.state)


@router.post("/connect")
async def connect(request: ConnectionRequest, authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    identity = _identity(authorization)
    user_id = identity["user_id"] if identity else None
    try:
        client = MCPClient(request.provider, request.bearer_token, user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Provider is not in the verified official catalog")
    if not client.configured:
        raise HTTPException(status_code=401, detail="Provider authorization is required")
    try:
        result = await client.call("tools/list", {})
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=f"Connection test failed: {exc}")
    if request.bearer_token and not user_id:
        _runtime_connections[request.provider] = {"token": request.bearer_token}
    tools = result.get("result", {}).get("tools", [])
    record("mcp_success", "integration_connected", {"provider": request.provider, "tool_count": len(tools)}, None, None)
    return {"connected": True, "provider": request.provider, "endpoint": client.endpoint, "tool_count": len(tools), "tools": tools}


@router.post("/disconnect")
async def disconnect(request: dict[str, str], authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    identity = _identity(authorization)
    provider = request.get("provider", "")
    if identity:
        from .integration_oauth import disconnect_connection
        disconnect_connection(identity["user_id"], provider)
    else:
        _runtime_connections.pop(provider, None)
    record("mcp_success", "integration_disconnected", {"provider": provider}, None, None)
    return {"disconnected": True, "provider": provider}


@router.get("/connections")
async def connections(authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    identity = _identity(authorization)
    if not identity:
        raise HTTPException(status_code=401, detail="Authentication required")
    from .integration_oauth import connection_summary
    return {"connections": connection_summary(identity["user_id"])}


@router.post("/discover-tools")
async def discover_tools(request: dict[str, str], authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    identity = _identity(authorization)
    try:
        client = MCPClient(request.get("provider", ""), user_id=identity["user_id"] if identity else None)
    except KeyError:
        raise HTTPException(status_code=404, detail="Provider is not in the verified official catalog")
    if not client.configured:
        raise HTTPException(status_code=401, detail="Provider authorization is required")
    try:
        result = await client.call("tools/list", {})
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    tools = result.get("result", {}).get("tools", [])
    return {"provider": request.get("provider"), "endpoint": client.endpoint, "tools": tools, "count": len(tools)}


@router.post("/mcp/call")
async def mcp_call(request: IntegrationRequest, authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    identity = _identity(authorization)
    try:
        client = MCPClient(request.provider, user_id=identity["user_id"] if identity else None)
    except KeyError:
        raise HTTPException(status_code=404, detail="Provider is not in the verified official catalog")
    if not client.configured:
        raise HTTPException(status_code=401, detail="Provider authorization is required")
    try:
        result = await client.call(request.method, request.params)
        record("mcp_success", "integration_tool_call", {"provider": request.provider, "method": request.method, "project_id": request.project_id, "entity_id": request.entity_id}, request.project_id, request.entity_id)
        return result
    except httpx.HTTPStatusError as exc:
        record("mcp_failure", "integration_tool_failure", {"provider": request.provider, "method": request.method, "status_code": exc.response.status_code}, request.project_id, request.entity_id)
        raise HTTPException(status_code=502, detail=f"Provider HTTP error: {exc.response.status_code}")
    except (httpx.HTTPError, RuntimeError) as exc:
        record("mcp_failure", "integration_tool_failure", {"provider": request.provider, "method": request.method, "error_type": type(exc).__name__}, request.project_id, request.entity_id)
        raise HTTPException(status_code=502, detail=str(exc))

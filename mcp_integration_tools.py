from __future__ import annotations
from typing import Any
import httpx
from mcp_integrations import MCP_PROVIDERS, public_provider_catalog, search_mcp_providers, provider_tool_help

async def _discover(endpoint: str, token: str | None = None) -> list[dict[str, Any]]:
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token: headers["Authorization"] = f"Bearer {token}"
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(endpoint, json=payload, headers=headers)
        r.raise_for_status()
        body = r.json()
    return body.get("result", {}).get("tools", [])

def register_integration_tools(mcp) -> None:
    @mcp.tool(name="search_fabrient_integrations", description="Search supported engineering MCP integrations by what the user needs done, such as CAD, PLM, documentation, repositories, or model inspection.")
    async def search_fabrient_integrations(query: str = "", limit: int = 10) -> dict[str, Any]:
        return {"query": query, "results": search_mcp_providers(query, limit)}

    @mcp.tool(name="get_integration_connection_link", description="Generate the lowest-friction connection instructions/link for a supported provider. Returns an official authorization URL when one is known; otherwise returns provider documentation or local connection details. Never exposes credentials.")
    async def get_integration_connection_link(provider: str) -> dict[str, Any]:
        p = MCP_PROVIDERS.get(provider)
        if not p: return {"error": "Unknown provider", "providers": public_provider_catalog()}
        if p.get("auth") == "public": return {"provider": provider, "mode": "public", "auth_url": p.get("endpoint"), "description": p["description"]}
        if p.get("auth") == "local": return {"provider": provider, "mode": "local", "endpoint": p.get("endpoint"), "docs": p.get("docs"), "description": p["description"]}
        return {"provider": provider, "mode": p.get("auth", "provider"), "docs": p.get("docs"), "description": p["description"], "message": "Use the provider's official OAuth/authorization flow. Fabrient does not guess authorization endpoints."}

    @mcp.tool(name="list_fabrient_mcp_integrations", description="List supported official MCP integrations and their short descriptions, authentication mode, and official documentation.")
    async def list_fabrient_mcp_integrations() -> dict[str, Any]:
        return {"providers": public_provider_catalog()}

    @mcp.tool(name="discover_connected_mcp_tools", description="Given an authorized MCP endpoint, discover its current tools dynamically. Use only an endpoint the user has authorized Fabrient to access.")
    async def discover_connected_mcp_tools(endpoint: str, bearer_token: str | None = None) -> dict[str, Any]:
        tools = await _discover(endpoint, bearer_token)
        return {"count": len(tools), "tools": tools}

    @mcp.tool(name="describe_mcp_integration", description="Return a concise description of a supported integration and how its tools are discovered.")
    async def describe_mcp_integration(provider: str) -> dict[str, Any]:
        try: return provider_tool_help(provider)
        except KeyError: return {"error": "Unknown provider"}

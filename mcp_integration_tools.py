from __future__ import annotations
from typing import Any
import httpx
from mcp_integrations import MCP_PROVIDERS, public_provider_catalog, search_mcp_providers, provider_tool_help

async def _discover(provider: str, token: str | None = None) -> list[dict[str, Any]]:
    p = MCP_PROVIDERS.get(provider)
    if not p:
        raise ValueError("Provider is not in Fabrient's verified official MCP catalog")
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
        r = await client.post(p["endpoint"], json=payload, headers=headers)
        r.raise_for_status()
        body = r.json()
    return body.get("result", {}).get("tools", [])

def register_integration_tools(mcp) -> None:
    @mcp.tool(name="search_fabrient_integrations", description="Search Fabrient's verified official MCP integrations by the job the user needs done, such as documentation or repository work. Only vendors with a concrete official MCP endpoint are returned.")
    async def search_fabrient_integrations(query: str = "", limit: int = 10) -> dict[str, Any]:
        return {"query": query, "results": search_mcp_providers(query, limit)}

    @mcp.tool(name="get_integration_connection_link", description="Return the verified official MCP endpoint and official documentation for a supported provider. Never invents OAuth URLs or accepts arbitrary custom MCP URLs.")
    async def get_integration_connection_link(provider: str) -> dict[str, Any]:
        p = MCP_PROVIDERS.get(provider)
        if not p:
            return {"error": "Provider is not in the verified official MCP catalog", "providers": public_provider_catalog()}
        return {"provider": provider, "name": p["name"], "endpoint": p["endpoint"], "authentication": p["auth"], "official_documentation": p["docs"], "description": p["description"]}

    @mcp.tool(name="list_fabrient_mcp_integrations", description="List only verified official remote MCP integrations, with each vendor-published MCP endpoint and a short description.")
    async def list_fabrient_mcp_integrations() -> dict[str, Any]:
        return {"providers": public_provider_catalog()}

    @mcp.tool(name="discover_connected_mcp_tools", description="Discover tools from a verified official MCP provider after authorization. Vendor tool names and schemas are read dynamically from tools/list.")
    async def discover_connected_mcp_tools(provider: str, bearer_token: str | None = None) -> dict[str, Any]:
        try:
            tools = await _discover(provider, bearer_token)
        except (ValueError, httpx.HTTPError) as exc:
            return {"error": str(exc)}
        return {"provider": provider, "count": len(tools), "tools": tools}

    @mcp.tool(name="search_connected_mcp_tools", description="Search the live tools exposed by a verified official MCP provider by what the user needs done. Returns vendor-provided names and descriptions.")
    async def search_connected_mcp_tools(provider: str, query: str, bearer_token: str | None = None, limit: int = 10) -> dict[str, Any]:
        try:
            tools = await _discover(provider, bearer_token)
        except (ValueError, httpx.HTTPError) as exc:
            return {"error": str(exc)}
        terms = [term.lower() for term in query.split() if term.strip()]
        matches = []
        for tool in tools:
            text = f"{tool.get('name','')} {tool.get('description','')}".lower()
            if not terms or all(term in text for term in terms):
                matches.append(tool)
        return {"provider": provider, "query": query, "count": len(matches[:limit]), "tools": matches[:limit]}

    @mcp.tool(name="describe_mcp_integration", description="Return a concise description, verified endpoint, authentication mode, and official documentation for a supported MCP integration.")
    async def describe_mcp_integration(provider: str) -> dict[str, Any]:
        try:
            return provider_tool_help(provider)
        except KeyError:
            return {"error": "Provider is not in the verified official MCP catalog"}

from __future__ import annotations
from typing import Any
import httpx
from mcp_integrations import MCP_PROVIDERS, public_provider_catalog, search_mcp_providers, provider_tool_help
FABRIENT_WEB_URL = "https://getfabrient.com"
async def _discover(provider: str, token: str | None = None) -> list[dict[str, Any]]:
    p = MCP_PROVIDERS.get(provider)
    if not p: raise ValueError("Provider is not in Fabrient's verified official MCP catalog")
    headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"}
    if token: headers["Authorization"]=f"Bearer {token}"
    async with httpx.AsyncClient(timeout=20.0,follow_redirects=False) as client:
        r=await client.post(p["endpoint"],json={"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}},headers=headers);r.raise_for_status();body=r.json()
    return body.get("result",{}).get("tools",[])
def register_integration_tools(mcp) -> None:
    @mcp.tool(name="search_fabrient_integrations",description="Search Fabrient's verified official integrations by the job the user needs done.")
    async def search_fabrient_integrations(query: str="",limit: int=10)->dict[str,Any]: return {"query":query,"results":search_mcp_providers(query,limit)}
    @mcp.tool(name="get_integration_connection_link",description="If an integration is not connected, return a simple Fabrient authorization link. The user never needs a client ID, client secret, API key, or MCP configuration.")
    async def get_integration_connection_link(provider: str)->dict[str,Any]:
        p=MCP_PROVIDERS.get(provider)
        if not p:return {"error":"Provider is not in the verified official MCP catalog","providers":public_provider_catalog()}
        if p["auth"]=="public":return {"provider":provider,"name":p["name"],"connected":True,"endpoint":p["endpoint"]}
        return {"provider":provider,"name":p["name"],"connected":False,"authorization_required":True,"connect_url":f"{FABRIENT_WEB_URL}/integrations?connect={provider}","endpoint":p["endpoint"],"authentication":p["auth"],"official_documentation":p["docs"],"message":"Open the connect link. Fabrient will handle OAuth and securely reuse the connection in both the web app and MCP."}
    @mcp.tool(name="list_fabrient_mcp_integrations",description="List verified official remote MCP integrations.")
    async def list_fabrient_mcp_integrations()->dict[str,Any]: return {"providers":public_provider_catalog()}
    @mcp.tool(name="discover_connected_mcp_tools",description="Discover tools from a verified official MCP provider after authorization.")
    async def discover_connected_mcp_tools(provider: str,bearer_token: str|None=None)->dict[str,Any]:
        try: tools=await _discover(provider,bearer_token)
        except (ValueError,httpx.HTTPError) as exc:return {"error":str(exc)}
        return {"provider":provider,"count":len(tools),"tools":tools}
    @mcp.tool(name="search_connected_mcp_tools",description="Search live tools exposed by a verified official MCP provider.")
    async def search_connected_mcp_tools(provider: str,query: str,bearer_token: str|None=None,limit: int=10)->dict[str,Any]:
        try:tools=await _discover(provider,bearer_token)
        except (ValueError,httpx.HTTPError) as exc:return {"error":str(exc)}
        terms=[x.lower() for x in query.split() if x.strip()];matches=[t for t in tools if not terms or all(x in f"{t.get('name','')} {t.get('description','')}".lower() for x in terms)]
        return {"provider":provider,"query":query,"count":len(matches[:limit]),"tools":matches[:limit]}
    @mcp.tool(name="describe_mcp_integration",description="Describe a supported MCP integration and its authentication model.")
    async def describe_mcp_integration(provider: str)->dict[str,Any]:
        try:return provider_tool_help(provider)
        except KeyError:return {"error":"Provider is not in the verified official MCP catalog"}

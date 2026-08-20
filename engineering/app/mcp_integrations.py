from __future__ import annotations
from typing import Any
MCP_PROVIDERS: dict[str, dict[str, Any]] = {
    "autodesk_fusion": {"name": "Autodesk Fusion", "description": "Drive a running Fusion desktop session for modeling and inspection.", "kind": "official", "auth": "local", "endpoint": "http://127.0.0.1:27182/mcp", "docs": "https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_FusionDesktopMcp_connecting_to_the_fusion_mcp_server_html"},
    "autodesk_fusion_data": {"name": "Autodesk Fusion Data", "description": "Manage Fusion cloud project data, hubs, folders, items and permissions.", "kind": "official", "auth": "oauth_discovery", "base_host": "https://developer.api.autodesk.com", "docs": "https://help.autodesk.com/view/fusion360/ENU/?guid=FMCP-OVERVIEW"},
    "autodesk_product_help": {"name": "Autodesk Product Help", "description": "Search official Autodesk documentation across 110+ products.", "kind": "official", "auth": "public", "endpoint": "https://developer.api.autodesk.com/knowledge/public/v1/mcp", "docs": "https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_KnowledgeMcp_autodesk_product_help_mcp_server_html"},
    "autodesk_revit": {"name": "Autodesk Revit", "description": "Access and inspect Revit model data through Autodesk's official MCP offering.", "kind": "official_preview", "auth": "provider", "docs": "https://help.autodesk.com/view/ADSKMCP/ENU/"},
    "autodesk_fusion_automation": {"name": "Autodesk Fusion Automation", "description": "Remote Fusion automation through Autodesk's private-beta MCP program.", "kind": "official_private_beta", "auth": "provider", "docs": "https://feedback.autodesk.com/key/FusionAutomationMCP"},
    "propel_plm": {"name": "Propel PLM", "description": "Query live Propel product records and perform governed PLM operations.", "kind": "official", "auth": "provider", "docs": "https://www.propelsoftware.com/products/propel-mcp"},
    "github": {"name": "GitHub", "description": "Repository, issue, pull-request and development workflow tools.", "kind": "official", "auth": "github", "docs": "https://github.com/github/github-mcp-server"},
}
def public_provider_catalog() -> list[dict[str, Any]]:
    return [{"id": pid, **p} for pid, p in sorted(MCP_PROVIDERS.items(), key=lambda x: x[1]["name"])]
def search_mcp_providers(query: str, limit: int = 10) -> list[dict[str, Any]]:
    terms = [t.lower() for t in query.split() if t.strip()]
    if not terms: return public_provider_catalog()[:limit]
    scored = []
    for pid, p in MCP_PROVIDERS.items():
        haystack = " ".join(str(p.get(k, "")) for k in ("name", "description", "kind", "auth", "docs")).lower()
        score = sum(2 if t in str(p.get("name", "")).lower() else 1 for t in terms if t in haystack)
        if score: scored.append((score, pid, p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [{"id": pid, **p} for _, pid, p in scored[:limit]]
def provider_tool_help(provider_id: str) -> dict[str, Any]:
    p = MCP_PROVIDERS.get(provider_id)
    if not p: raise KeyError(provider_id)
    return {"provider": provider_id, "name": p["name"], "description": p["description"], "authentication": p["auth"], "official_documentation": p["docs"], "endpoint": p.get("endpoint"), "note": "Vendor tool names are discovered dynamically with MCP tools/list after connection; Fabrient does not guess or hard-code vendor tool names."}

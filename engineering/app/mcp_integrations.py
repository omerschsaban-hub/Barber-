from __future__ import annotations
from typing import Any

# Production catalog is intentionally strict: only MCP servers with a concrete,
# vendor-published endpoint are included. Local-only servers and vendors that
# announce MCP without publishing a concrete endpoint are excluded until an
# official endpoint is documented.
MCP_PROVIDERS: dict[str, dict[str, Any]] = {
    "autodesk_product_help": {
        "name": "Autodesk Product Help",
        "description": "Search Autodesk's live product documentation through the official read-only MCP server.",
        "kind": "official_remote",
        "auth": "public",
        "endpoint": "https://developer.api.autodesk.com/knowledge/public/v1/mcp",
        "docs": "https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_KnowledgeMcp_autodesk_product_help_mcp_server_html",
    },
    "github": {
        "name": "GitHub",
        "description": "Use GitHub's official remote MCP server for repositories, issues, pull requests, workflows, and code context.",
        "kind": "official_remote",
        "auth": "oauth_or_pat",
        "endpoint": "https://api.githubcopilot.com/mcp/",
        "docs": "https://github.com/github/github-mcp-server",
    },
}

def public_provider_catalog() -> list[dict[str, Any]]:
    return [{"id": pid, **p} for pid, p in sorted(MCP_PROVIDERS.items(), key=lambda x: x[1]["name"])]

def search_mcp_providers(query: str, limit: int = 10) -> list[dict[str, Any]]:
    terms = [t.lower() for t in query.split() if t.strip()]
    catalog = public_provider_catalog()
    if not terms:
        return catalog[:limit]
    scored = []
    for pid, p in MCP_PROVIDERS.items():
        haystack = " ".join(str(p.get(k, "")) for k in ("name", "description", "kind", "auth", "docs", "endpoint")).lower()
        score = sum(2 if t in str(p.get("name", "")).lower() else 1 for t in terms if t in haystack)
        if score:
            scored.append((score, pid, p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [{"id": pid, **p} for _, pid, p in scored[:limit]]

def provider_tool_help(provider_id: str) -> dict[str, Any]:
    p = MCP_PROVIDERS.get(provider_id)
    if not p:
        raise KeyError(provider_id)
    return {
        "provider": provider_id,
        "name": p["name"],
        "description": p["description"],
        "authentication": p["auth"],
        "official_documentation": p["docs"],
        "endpoint": p["endpoint"],
        "note": "Vendor tool names are discovered dynamically with MCP tools/list after authorized connection; Fabrient does not guess vendor tool names.",
    }

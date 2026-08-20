from __future__ import annotations
from typing import Any

# Strict production catalog: every entry has a concrete, vendor-published remote MCP URL.
MCP_PROVIDERS: dict[str, dict[str, Any]] = {
    "autodesk_product_help": {"name": "Autodesk Product Help", "description": "Search Autodesk's official product documentation through a public read-only MCP server.", "kind": "official_remote", "auth": "public", "endpoint": "https://developer.api.autodesk.com/knowledge/public/v1/mcp", "docs": "https://help.autodesk.com/view/ADSKMCP/ENU/?guid=ADSKMCP_KnowledgeMcp_autodesk_product_help_mcp_server_html"},
    "github": {"name": "GitHub", "description": "Work with repositories, issues, pull requests, code, and development workflows through GitHub's official MCP server.", "kind": "official_remote", "auth": "oauth_or_pat", "endpoint": "https://api.githubcopilot.com/mcp/", "docs": "https://github.com/github/github-mcp-server"},
    "linear": {"name": "Linear", "description": "Find, create, and update Linear issues, projects, comments, and related project-management data.", "kind": "official_remote", "auth": "oauth_or_token", "endpoint": "https://mcp.linear.app/mcp", "docs": "https://linear.app/docs/mcp"},
    "stripe": {"name": "Stripe", "description": "Interact with authorized Stripe API capabilities for payments, customers, products, invoices, and related account data.", "kind": "official_remote", "auth": "oauth_or_api_key", "endpoint": "https://mcp.stripe.com", "docs": "https://github.com/stripe/ai/tree/main/tools/modelcontextprotocol"},
    "cloudflare": {"name": "Cloudflare", "description": "Manage and inspect authorized Cloudflare developer-platform resources through Cloudflare's managed MCP server.", "kind": "official_remote", "auth": "oauth_or_token", "endpoint": "https://mcp.cloudflare.com/mcp", "docs": "https://developers.cloudflare.com/agents/model-context-protocol/cloudflare/servers-for-cloudflare/"},
    "cloudflare_docs": {"name": "Cloudflare Documentation", "description": "Search current Cloudflare developer documentation and product guidance.", "kind": "official_remote", "auth": "public", "endpoint": "https://docs.mcp.cloudflare.com/mcp", "docs": "https://developers.cloudflare.com/workers/get-started/prompting/"},
    "cloudflare_observability": {"name": "Cloudflare Observability", "description": "Inspect authorized Cloudflare logs and analytics to investigate application behavior and operational issues.", "kind": "official_remote", "auth": "oauth_or_token", "endpoint": "https://observability.mcp.cloudflare.com/mcp", "docs": "https://developers.cloudflare.com/workers/get-started/prompting/"},
    "netlify": {"name": "Netlify", "description": "Inspect and manage authorized Netlify sites, deployments, and hosting workflows through Netlify's remote MCP server.", "kind": "official_remote", "auth": "oauth", "endpoint": "https://netlify-mcp.netlify.app/mcp", "docs": "https://docs.netlify.com/build/build-with-ai/agent-setup-guides/agent-setup-overview/"},
    "notion": {"name": "Notion", "description": "Search and work with authorized Notion workspace content through Notion's hosted MCP server.", "kind": "official_remote", "auth": "oauth", "endpoint": "https://mcp.notion.so/mcp", "docs": "https://developers.cloudflare.com/agents/model-context-protocol/apis/client-api/"},
    "vercel": {"name": "Vercel", "description": "Work with authorized Vercel projects and deployment workflows through Vercel's remote MCP server.", "kind": "official_remote", "auth": "oauth", "endpoint": "https://mcp.vercel.com/", "docs": "https://vercel.com/docs/mcp"},
}

def public_provider_catalog() -> list[dict[str, Any]]:
    return [{"id": pid, **p} for pid, p in sorted(MCP_PROVIDERS.items(), key=lambda x: x[1]["name"])]

def search_mcp_providers(query: str, limit: int = 10) -> list[dict[str, Any]]:
    terms = [t.lower() for t in query.split() if t.strip()]
    catalog = public_provider_catalog()
    if not terms: return catalog[:limit]
    scored = []
    for pid, p in MCP_PROVIDERS.items():
        haystack = " ".join(str(p.get(k, "")) for k in ("name", "description", "kind", "auth", "docs", "endpoint")).lower()
        score = sum(2 if t in str(p.get("name", "")).lower() else 1 for t in terms if t in haystack)
        if score: scored.append((score, pid, p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [{"id": pid, **p} for _, pid, p in scored[:limit]]

def provider_tool_help(provider_id: str) -> dict[str, Any]:
    p = MCP_PROVIDERS.get(provider_id)
    if not p: raise KeyError(provider_id)
    return {"provider": provider_id, "name": p["name"], "description": p["description"], "authentication": p["auth"], "official_documentation": p["docs"], "endpoint": p["endpoint"], "note": "Vendor tools are discovered dynamically with MCP tools/list after authorization; Fabrient does not guess vendor tool names."}

from __future__ import annotations

import os
from typing import Any

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from server import CAPABILITY_REGISTRY, app as mcp_app
from auth_db import user_from_bearer, _pool

PROJECT_ID = "projb138a8db"
PRO_ENTITLEMENT = "create_an_app_called_fabrinat_pro"
MCP_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "fabrient-mcp.onrender.com")
MCP_RESOURCE_URL = os.getenv("FABRIENT_MCP_RESOURCE_URL", f"https://{MCP_HOST}/mcp").rstrip("/")
MCP_RESOURCE_METADATA_URL = f"https://{MCP_HOST}/.well-known/oauth-protected-resource/mcp"
OAUTH_ISSUER = os.getenv("FABRIENT_MCP_OAUTH_ISSUER", f"https://{MCP_HOST}").rstrip("/")
OAUTH_SCOPES = ["openid", "email", "profile"]

FREE_TOOL_NAMES = {
    "inspect_part", "analyze_dfm", "verify_fixes", "validate_material",
    "validate_machine_envelope", "validate_dimension", "check_wall_thickness",
    "check_clearances", "check_holes", "check_overhangs", "check_orientation",
    "check_tolerances", "check_fit", "check_first_layer", "check_bed_adhesion",
    "check_revision_consistency", "compare_revisions", "trace_provenance",
    "build_inspection_plan", "estimate_risk", "next_experiment",
}

TOOL_BY_NAME = {name: (description, path) for name, description, path in CAPABILITY_REGISTRY}
if not FREE_TOOL_NAMES.issubset(TOOL_BY_NAME):
    raise RuntimeError("Free MCP tool allowlist contains an unknown tool")


def _billing_state(user_id: str) -> bool:
    with _pool().connection() as conn:
        row = conn.execute(
            """select 1 from billing_entitlements
               where user_id=%s and entitlement_id=%s and active=true
                 and (expires_at is null or expires_at>now())
               limit 1""",
            (user_id, PRO_ENTITLEMENT),
        ).fetchone()
        return row is not None


def _authenticated_user(request: Request) -> dict[str, Any] | None:
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    identity = user_from_bearer(authorization[7:].strip())
    if not identity:
        return None
    try:
        identity["pro"] = _billing_state(identity["user_id"])
        return identity
    except Exception:
        return None


async def capabilities(request: Request) -> JSONResponse:
    identity = _authenticated_user(request)
    if identity is None:
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=401,
            headers={"WWW-Authenticate": f'Bearer resource_metadata="{MCP_RESOURCE_METADATA_URL}", scope="mcp:use"'},
        )
    available = list(CAPABILITY_REGISTRY) if identity["pro"] else [
        item for item in CAPABILITY_REGISTRY if item[0] in FREE_TOOL_NAMES
    ]
    return JSONResponse({
        "name": "Fabrient Engineering",
        "authenticated": True,
        "pro": identity["pro"],
        "entitlement": PRO_ENTITLEMENT,
        "tool_count": len(available),
        "total_tool_count": len(CAPABILITY_REGISTRY),
        "tools": [name for name, _, _ in available],
        "gated_tool_count": len(CAPABILITY_REGISTRY) - len(available),
        "registry_authoritative": True,
        "access_policy": "free_core_plus_pro_advanced_tools",
        "oauth": {"issuer": OAUTH_ISSUER, "resource": MCP_RESOURCE_URL, "scopes": OAUTH_SCOPES},
    })


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "fabrient-mcp-auth-wrapper", "tool_count": len(CAPABILITY_REGISTRY)})


async def protected_resource(_: Request) -> JSONResponse:
    return JSONResponse({
        "resource": MCP_RESOURCE_URL,
        "authorization_servers": [OAUTH_ISSUER],
        "scopes_supported": OAUTH_SCOPES,
        "bearer_methods_supported": ["header"],
    })


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/health", "/", "/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"}:
            return await call_next(request)
        if request.url.path == "/capabilities":
            return await call_next(request)
        if request.url.path.startswith("/mcp"):
            identity = _authenticated_user(request)
            if identity is None:
                return JSONResponse(
                    {"error": "Unauthorized", "message": "A valid Fabrient OAuth/session bearer token is required."},
                    status_code=401,
                    headers={"WWW-Authenticate": f'Bearer resource_metadata="{MCP_RESOURCE_METADATA_URL}", scope="mcp:use"'},
                )
        return await call_next(request)


app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/capabilities", capabilities, methods=["GET"]),
        Route("/.well-known/oauth-protected-resource", protected_resource, methods=["GET"]),
        Route("/.well-known/oauth-protected-resource/mcp", protected_resource, methods=["GET"]),
        Mount("/", app=mcp_app),
    ],
)
app.add_middleware(AuthMiddleware)

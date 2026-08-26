from __future__ import annotations

import os
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

# Render starts this module as services.mcp.auth_server, so the MCP server must
# be imported as a package-relative module. The old bare `from server` import
# worked only when the process cwd happened to contain services/mcp.
from .server import CAPABILITY_REGISTRY, app as mcp_app

PROJECT_ID = os.getenv("REVENUECAT_PROJECT_ID", "projb138a8db")
PRO_ENTITLEMENT = os.getenv("FABRIENT_PRO_ENTITLEMENT", "create_an_app_called_fabrinat_pro")
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "https://gphmefejeqvlemzvmade.supabase.co").rstrip("/")
SUPABASE_AUTH_ISSUER = f"{SUPABASE_URL}/auth/v1"
SUPABASE_OAUTH_DISCOVERY = f"{SUPABASE_URL}/.well-known/oauth-authorization-server/auth/v1"
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
MCP_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "fabrient-mcp.onrender.com")
MCP_RESOURCE_URL = os.getenv("FABRIENT_MCP_RESOURCE_URL", f"https://{MCP_HOST}/mcp").rstrip("/")
MCP_RESOURCE_METADATA_URL = f"https://{MCP_HOST}/.well-known/oauth-protected-resource"
OAUTH_SCOPES = ["openid", "email"]

async def _authenticated_user(request: Request) -> dict[str, Any] | None:
    authorization = request.headers.get("authorization")
    if not authorization or not authorization.lower().startswith("bearer ") or not SUPABASE_ANON_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{SUPABASE_AUTH_ISSUER}/user", headers={"apikey": SUPABASE_ANON_KEY, "Authorization": authorization})
            if response.status_code != 200:
                return None
            user = response.json()
            user_id = user.get("id")
            if not user_id:
                return None
            return {"user_id": user_id, "email": str(user.get("email") or "").lower(), "email_verified": bool(user.get("email_confirmed_at") or user.get("confirmed_at"))}
    except (httpx.HTTPError, ValueError):
        return None

async def capabilities(request: Request) -> JSONResponse:
    identity = await _authenticated_user(request)
    if identity is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{MCP_RESOURCE_METADATA_URL}"'})
    return JSONResponse({"name": "Fabrient Engineering", "authenticated": True, "account": identity, "tool_count": len(CAPABILITY_REGISTRY), "total_tool_count": len(CAPABILITY_REGISTRY), "tools": [x[0] for x in CAPABILITY_REGISTRY], "registry_authoritative": True, "oauth": {"issuer": SUPABASE_AUTH_ISSUER, "discovery": SUPABASE_OAUTH_DISCOVERY, "resource": MCP_RESOURCE_URL, "scopes": OAUTH_SCOPES, "login_method": "email_otp"}})

async def account(request: Request) -> JSONResponse:
    identity = await _authenticated_user(request)
    if identity is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{MCP_RESOURCE_METADATA_URL}"'})
    return JSONResponse({"account": identity})

async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "fabrient-mcp-auth-wrapper", "tool_count": len(CAPABILITY_REGISTRY), "oauth_discovery": SUPABASE_OAUTH_DISCOVERY, "login_method": "email_otp"})

async def protected_resource(_: Request) -> JSONResponse:
    return JSONResponse({"resource": MCP_RESOURCE_URL, "authorization_servers": [SUPABASE_AUTH_ISSUER], "scopes_supported": OAUTH_SCOPES, "bearer_methods_supported": ["header"]})

async def oauth_discovery(_: Request) -> JSONResponse:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(SUPABASE_OAUTH_DISCOVERY)
        response.raise_for_status()
        metadata = response.json()
        metadata["scopes_supported"] = OAUTH_SCOPES
        return JSONResponse(metadata)

async def request_code(request: Request) -> JSONResponse:
    if not SUPABASE_ANON_KEY:
        return JSONResponse({"error": "Email authentication is not configured."}, status_code=503)
    try:
        body = await request.json()
        email = str(body.get("email") or "").strip().lower()
        if not email or "@" not in email or len(email) > 320:
            return JSONResponse({"error": "Enter a valid email address."}, status_code=400)
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(f"{SUPABASE_AUTH_ISSUER}/otp", headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"}, json={"email": email, "create_user": True})
        if response.status_code >= 400:
            return JSONResponse({"error": "We couldn't send the code. Please try again."}, status_code=502)
        return JSONResponse({"ok": True, "message": "Code sent. Check your email."})
    except (ValueError, httpx.HTTPError):
        return JSONResponse({"error": "We couldn't send the code. Please try again."}, status_code=400)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public = {"/health", "/", "/capabilities", "/account", "/request-code", "/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp", "/.well-known/oauth-authorization-server"}
        if request.url.path in public:
            return await call_next(request)
        if request.url.path.startswith("/mcp"):
            identity = await _authenticated_user(request)
            if identity is None:
                return JSONResponse({"error": "Unauthorized"}, status_code=401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{MCP_RESOURCE_METADATA_URL}"'})
            request.state.fabrient_account = identity
        return await call_next(request)

app = Starlette(routes=[Route("/health", health, methods=["GET"]), Route("/capabilities", capabilities, methods=["GET"]), Route("/account", account, methods=["GET"]), Route("/request-code", request_code, methods=["POST"]), Route("/.well-known/oauth-protected-resource", protected_resource, methods=["GET"]), Route("/.well-known/oauth-protected-resource/mcp", protected_resource, methods=["GET"]), Route("/.well-known/oauth-authorization-server", oauth_discovery, methods=["GET"]), Mount("/", app=mcp_app)])
app.add_middleware(AuthMiddleware)

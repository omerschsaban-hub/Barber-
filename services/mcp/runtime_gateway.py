from __future__ import annotations

import os
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

# The MCP server is an interface layer. It must not independently decide identity,
# billing, or authorization. The engineering service is the source of truth.
os.environ["FABRIENT_DISABLE_PRODUCTION_AUTH"] = "true"

from . import auth_server as oauth  # noqa: E402
from . import server as mcp_server  # noqa: E402

ENGINE_URL = os.getenv("FABRIENT_ENGINE_URL", "https://fabrient-engineering.onrender.com").rstrip("/")
MCP_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "fabrient-mcp.onrender.com")
RESOURCE = os.getenv("FABRIENT_MCP_RESOURCE_URL", f"https://{MCP_HOST}/mcp").rstrip("/")
ISSUER = os.getenv("FABRIENT_MCP_OAUTH_ISSUER", f"https://{MCP_HOST}").rstrip("/")
RESOURCE_METADATA = f"{ISSUER}/.well-known/oauth-protected-resource"
SCOPES = {"openid", "email", "profile", "mcp:use"}
CORE_TOOLS = (
    "inspect_part", "analyze_dfm", "verify_fixes", "validate_material", "validate_machine_envelope",
    "validate_dimension", "check_wall_thickness", "check_clearances", "check_holes", "check_overhangs",
    "check_orientation", "check_tolerances", "check_fit", "check_first_layer", "check_bed_adhesion",
)
RATE_LIMIT = max(10, int(os.getenv("FABRIENT_MCP_REQUESTS_PER_MINUTE", "120")))
_WINDOW = 60.0
_buckets: dict[str, list[float]] = {}
_current_token: ContextVar[str | None] = ContextVar("fabrient_mcp_bearer", default=None)

# Keep the full registry in source for staged promotion, but expose only the small,
# proven core to MCP clients. Additional tools are promoted after semantic E2E tests.
for _tool in list(mcp_server.mcp._tool_manager.list_tools()):
    if _tool.name not in CORE_TOOLS:
        mcp_server.mcp.remove_tool(_tool.name)


async def _engine_get(path: str, token: str) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(f"{ENGINE_URL}{path}", headers={"Authorization": f"Bearer {token}"})
        if response.status_code != 200:
            return None
        data = response.json()
        return data if isinstance(data, dict) else None
    except (httpx.HTTPError, ValueError):
        return None


async def _engine_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(f"{ENGINE_URL}/health")
        return response.status_code == 200
    except httpx.HTTPError:
        return False


async def _identity(request: Request) -> dict[str, Any] | None:
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        return None
    token = authorization[7:].strip()
    data = await _engine_get("/auth/me", token)
    if not data or not isinstance(data.get("user"), dict):
        return None
    user = dict(data["user"])
    user["scope"] = "openid email profile mcp:use"
    user["access_token"] = token
    return user


async def _access(token: str) -> dict[str, Any] | None:
    return await _engine_get("/v1/mcp/access", token)


class ForwardBackendAuthClient(httpx.AsyncClient):
    async def request(self, method: str, url: Any, *args: Any, **kwargs: Any) -> httpx.Response:
        token = _current_token.get()
        if token and str(url).startswith(ENGINE_URL):
            headers = httpx.Headers(kwargs.get("headers"))
            headers["Authorization"] = f"Bearer {token}"
            kwargs["headers"] = headers
        return await super().request(method, url, *args, **kwargs)


# server.py resolves httpx.AsyncClient when each tool executes. This carries the
# already-validated MCP bearer token into the shared engineering service.
httpx.AsyncClient = ForwardBackendAuthClient  # type: ignore[assignment]


def _allow_rate(key: str) -> tuple[bool, int]:
    import time
    now = time.monotonic()
    bucket = _buckets.setdefault(key, [])
    cutoff = now - _WINDOW
    while bucket and bucket[0] <= cutoff:
        bucket.pop(0)
    if len(bucket) >= RATE_LIMIT:
        return False, 60
    bucket.append(now)
    return True, max(1, int(_WINDOW - (now - bucket[0]))) if bucket else 60


async def health(_: Request):
    return JSONResponse({
        "status": "ok",
        "service": "fabrient-mcp",
        "architecture": "mcp-interface-over-shared-engine",
        "resource": RESOURCE,
        "engine_url": ENGINE_URL,
        "core_tool_count": len(CORE_TOOLS),
        "total_registry_count": len(mcp_server.CAPABILITY_REGISTRY),
    }, headers={"Cache-Control": "no-store"})


async def ready(_: Request):
    if not await _engine_health():
        return JSONResponse({"status": "not_ready", "reason": "engineering_backend_unavailable"}, 503, headers={"Cache-Control": "no-store"})
    return JSONResponse({"status": "ready", "service": "fabrient-mcp", "engine": "ready", "core_tool_count": len(CORE_TOOLS)}, headers={"Cache-Control": "no-store"})


async def capabilities(request: Request):
    identity = await _identity(request)
    if identity is None:
        return JSONResponse({"error": "unauthorized"}, 401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{RESOURCE_METADATA}", scope="mcp:use"'})
    access = await _access(identity["access_token"])
    if access is None:
        return JSONResponse({"error": "authorization_unavailable"}, 503)
    plan = str(access.get("plan") or "free")
    return JSONResponse({
        "name": "Fabrient Engineering",
        "authenticated": True,
        "plan": plan,
        "tools": list(CORE_TOOLS),
        "tool_count": len(CORE_TOOLS),
        "total_registry_count": len(mcp_server.CAPABILITY_REGISTRY),
        "gated_tool_count": len(mcp_server.CAPABILITY_REGISTRY) - len(CORE_TOOLS),
        "access_policy": "reliable_core_first",
        "architecture": "MCP is transport/interface; Engineering API owns auth, billing, business logic, and Postgres",
    }, headers={"Cache-Control": "private, max-age=5"})


async def account(request: Request):
    identity = await _identity(request)
    if identity is None:
        return JSONResponse({"error": "unauthorized"}, 401)
    return JSONResponse({"user": {k: v for k, v in identity.items() if k != "access_token"}}, headers={"Cache-Control": "private, max-age=5"})


class MCPGatewayAuth(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public = {
            "/", "/health", "/ready", "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp", "/.well-known/oauth-authorization-server",
            "/oauth/register", "/oauth/authorize", "/oauth/token", "/oauth/revoke",
        }
        if request.url.path in public or request.url.path.startswith("/oauth/details/") or request.url.path.startswith("/oauth/decide/"):
            return await call_next(request)
        if request.url.path in {"/capabilities", "/account"} or request.url.path.startswith("/mcp"):
            identity = await _identity(request)
            if identity is None:
                return JSONResponse({"error": "unauthorized", "request_id": request.headers.get("x-request-id")}, 401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{RESOURCE_METADATA}", scope="mcp:use"'})
            if "mcp:use" not in set(str(identity.get("scope") or "").split()):
                return JSONResponse({"error": "insufficient_scope", "scope": "mcp:use"}, 403)
            allowed, retry = _allow_rate(f"user:{identity['id']}")
            if not allowed:
                return JSONResponse({"error": "rate_limited", "retry_after_seconds": retry}, 429, headers={"Retry-After": str(retry)})
            token = identity["access_token"]
            reset = _current_token.set(token)
            try:
                response = await call_next(request)
            finally:
                _current_token.reset(reset)
            response.headers["X-Request-ID"] = request.headers.get("x-request-id", "") or "mcp-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
            response.headers["Cache-Control"] = "no-store"
            return response
        return await call_next(request)


routes = [
    Route("/", health), Route("/health", health), Route("/ready", ready), Route("/capabilities", capabilities), Route("/account", account),
    Route("/.well-known/oauth-protected-resource", oauth.protected),
    Route("/.well-known/oauth-protected-resource/mcp", oauth.protected),
    Route("/.well-known/oauth-authorization-server", oauth.metadata),
    Route("/oauth/register", oauth.register, methods=["POST"]),
    Route("/oauth/authorize", oauth.authorize), Route("/oauth/token", oauth.token, methods=["POST"]),
    Route("/oauth/revoke", oauth.revoke, methods=["POST"]), Route("/oauth/details/{id}", oauth.details),
    Route("/oauth/decide/{id}/{decision}", oauth.decide, methods=["POST"]),
    Mount("/", app=mcp_server.app),
]

app = Starlette(routes=routes)
app.add_middleware(MCPGatewayAuth)

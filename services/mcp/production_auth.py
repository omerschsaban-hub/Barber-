from __future__ import annotations

import os
import time
import uuid
from collections import defaultdict, deque
from typing import Any, Callable

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from .auth_db import user_from_bearer, _pool

PROJECT_ID = os.getenv("REVENUECAT_PROJECT_ID", "projb138a8db")
HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "fabrient-mcp.onrender.com")
ISSUER = os.getenv("FABRIENT_MCP_OAUTH_ISSUER", f"https://{HOST}").rstrip("/")
RESOURCE = os.getenv("FABRIENT_MCP_RESOURCE_URL", f"https://{HOST}/mcp").rstrip("/")
RESOURCE_METADATA = f"{ISSUER}/.well-known/oauth-protected-resource"

PUBLIC_DOMAINS = {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "yahoo.com", "icloud.com", "proton.me", "protonmail.com", "aol.com"}
ENTERPRISE_DOMAINS = {x.strip().lower() for x in os.getenv("FABRIENT_ENTERPRISE_DOMAINS", "").split(",") if x.strip()}
STARTUP_DOMAINS = {x.strip().lower() for x in os.getenv("FABRIENT_STARTUP_DOMAINS", "").split(",") if x.strip()}

FREE_TOOL_NAMES = {
    "inspect_part", "analyze_dfm", "verify_fixes", "validate_material", "validate_machine_envelope", "validate_dimension",
    "check_wall_thickness", "check_clearances", "check_holes", "check_overhangs", "check_orientation", "check_tolerances",
    "check_fit", "check_first_layer", "check_bed_adhesion", "check_revision_consistency", "compare_revisions", "trace_provenance",
    "build_inspection_plan", "estimate_risk", "next_experiment",
}
RATE_LIMIT = max(10, int(os.getenv("FABRIENT_MCP_REQUESTS_PER_MINUTE", "120")))
_WINDOW = 60.0
_buckets: dict[str, deque[float]] = defaultdict(deque)


def _segment(user: dict[str, Any]) -> tuple[str, str, str]:
    metadata = user.get("user_metadata") or {}
    app_metadata = user.get("app_metadata") or {}
    raw = str(metadata.get("account_type") or metadata.get("company_type") or metadata.get("organization_type") or metadata.get("segment") or app_metadata.get("account_type") or app_metadata.get("segment") or "").strip().lower()
    raw = {"hobby": "hobbyist", "solo": "hobbyist", "individual": "hobbyist", "company": "startup"}.get(raw, raw)
    email = str(user.get("email") or "").lower()
    domain = email.rsplit("@", 1)[-1] if "@" in email else ""
    if raw in {"enterprise", "startup", "hobbyist"}:
        return raw, "explicit_account_metadata", "high"
    if domain in ENTERPRISE_DOMAINS:
        return "enterprise", "configured_enterprise_domain", "high"
    if domain in STARTUP_DOMAINS:
        return "startup", "configured_startup_domain", "high"
    if domain in PUBLIC_DOMAINS:
        return "hobbyist", "consumer_email_domain", "medium"
    if domain:
        return "startup", "custom_domain_default", "low"
    return "unknown", "insufficient_identity_data", "low"


def _identity(request: Request) -> dict[str, Any] | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    try:
        user = user_from_bearer(auth[7:].strip())
        if not user:
            return None
        uid = str(user["user_id"])
        with _pool().connection() as conn:
            rows = conn.execute("""select entitlement_id from billing_entitlements
                where user_id=%s and active=true and (expires_at is null or expires_at>now())
                order by entitlement_id""", (uid,)).fetchall()
        entitlements = [str(row["entitlement_id"] if isinstance(row, dict) else row[0]) for row in rows]
        paid = bool(entitlements)
        segment, basis, confidence = _segment(user)
        return {"user_id": uid, "email": str(user.get("email") or "").lower(), "email_verified": True, "name": user.get("display_name"), "paid": paid, "plan": "pro" if paid else "free", "billing_status": "verified", "billing_source": "owned_postgres" if entitlements else "owned_postgres_none", "entitlements": entitlements, "segment": segment, "segment_basis": basis, "segment_confidence": confidence}
    except (ValueError, KeyError, RuntimeError):
        return None


class ProductionMCPAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, registry: tuple[tuple[str, str, str], ...]):
        super().__init__(app)
        self.registry = registry

    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.fabrient_request_id = request_id
        path = request.url.path
        public = path in {"/", "/health", "/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp", "/.well-known/oauth-authorization-server"}
        identity = None
        if not public or path in {"/capabilities", "/account"}:
            identity = _identity(request)
            key = f"user:{identity['user_id']}" if identity else f"ip:{request.client.host if request.client else 'unknown'}"
            now = time.monotonic()
            bucket = _buckets[key]
            while bucket and bucket[0] <= now - _WINDOW:
                bucket.popleft()
            if len(bucket) >= RATE_LIMIT:
                return JSONResponse({"error": "rate_limited", "request_id": request_id}, 429, headers={"Retry-After": "60", "X-Request-ID": request_id})
            bucket.append(now)
        if path.startswith("/mcp") and identity is None:
            return JSONResponse({"error": "unauthorized", "message": "A valid Fabrient OAuth access token is required.", "request_id": request_id}, 401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{RESOURCE_METADATA}"', "X-Request-ID": request_id})
        if identity is not None:
            request.state.fabrient_account = identity
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers.setdefault("Cache-Control", "no-store")
        return response


async def protected_resource(_: Request):
    return JSONResponse({"resource": RESOURCE, "authorization_servers": [ISSUER], "scopes_supported": ["openid", "email", "profile"], "bearer_methods_supported": ["header"]}, headers={"Cache-Control": "public, max-age=300"})


async def oauth_discovery(_: Request):
    # Never fetch the discovery URL from itself. This endpoint is authoritative and static.
    body = {"issuer": ISSUER, "authorization_endpoint": f"{ISSUER}/oauth/authorize", "token_endpoint": f"{ISSUER}/oauth/token", "revocation_endpoint": f"{ISSUER}/oauth/revoke", "response_types_supported": ["code"], "grant_types_supported": ["authorization_code"], "code_challenge_methods_supported": ["S256"], "scopes_supported": ["openid", "email", "profile", "mcp:use"]}
    return JSONResponse(body, headers={"Cache-Control": "public, max-age=300"})


async def health(_: Request):
    return JSONResponse({"status": "ok", "service": "fabrient-mcp", "oauth": {"issuer": ISSUER, "discovery": f"{ISSUER}/.well-known/oauth-authorization-server"}, "resource": RESOURCE}, headers={"Cache-Control": "public, max-age=30"})


def wrap_app(mcp_app: Any, registry: tuple[tuple[str, str, str], ...]) -> Starlette:
    async def capabilities(request: Request):
        identity = _identity(request)
        if identity is None:
            return JSONResponse({"error": "unauthorized"}, 401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{RESOURCE_METADATA}"'})
        available = list(registry) if identity["paid"] is True else [x for x in registry if x[0] in FREE_TOOL_NAMES]
        return JSONResponse({"name": "Fabrient Engineering", "authenticated": True, "account": {k: identity[k] for k in ("user_id", "email", "email_verified", "paid", "plan", "billing_status", "entitlements", "segment", "segment_basis", "segment_confidence")}, "tool_count": len(available), "total_tool_count": len(registry), "tools": [x[0] for x in available], "gated_tool_count": len(registry) - len(available), "access_policy": "free_core_plus_paid_advanced_tools"}, headers={"Cache-Control": "private, max-age=5"})

    async def account(request: Request):
        identity = _identity(request)
        if identity is None:
            return JSONResponse({"error": "unauthorized"}, 401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{RESOURCE_METADATA}"'})
        return JSONResponse({"account": identity}, headers={"Cache-Control": "private, max-age=5"})

    wrapper = Starlette(lifespan=getattr(getattr(mcp_app, "router", None), "lifespan_context", None), routes=[
        Route("/health", health, methods=["GET"]),
        Route("/capabilities", capabilities, methods=["GET"]),
        Route("/account", account, methods=["GET"]),
        Route("/.well-known/oauth-protected-resource", protected_resource, methods=["GET"]),
        Route("/.well-known/oauth-protected-resource/mcp", protected_resource, methods=["GET"]),
        Route("/.well-known/oauth-authorization-server", oauth_discovery, methods=["GET"]),
    ])
    wrapper.mount("/", mcp_app)
    wrapper.add_middleware(ProductionMCPAuthMiddleware, registry=registry)
    return wrapper

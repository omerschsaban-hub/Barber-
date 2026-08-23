from __future__ import annotations

import os
import time
import uuid
from collections import defaultdict, deque
from typing import Any, Callable

import httpx
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route


PROJECT_ID = os.getenv("REVENUECAT_PROJECT_ID", "projb138a8db")
REVENUECAT_SECRET = os.getenv("REVENUECAT_SECRET_API_KEY") or os.getenv("REVENUECAT_API_KEY")
PRO_ENTITLEMENT = os.getenv("FABRIENT_PRO_ENTITLEMENT", "create_an_app_called_fabrinat_pro").lower()
SUPABASE_URL = (os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "https://gphmefejeqvlemzvmade.supabase.co").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
ISSUER = f"{SUPABASE_URL}/auth/v1"
DISCOVERY = f"{SUPABASE_URL}/.well-known/oauth-authorization-server/auth/v1"
HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "fabrient-mcp.onrender.com")
RESOURCE = os.getenv("FABRIENT_MCP_RESOURCE_URL", f"https://{HOST}/mcp").rstrip("/")
RESOURCE_METADATA = f"https://{HOST}/.well-known/oauth-protected-resource"

PUBLIC_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com",
    "yahoo.com", "icloud.com", "proton.me", "protonmail.com", "aol.com",
}
ENTERPRISE_DOMAINS = {x.strip().lower() for x in os.getenv("FABRIENT_ENTERPRISE_DOMAINS", "").split(",") if x.strip()}
STARTUP_DOMAINS = {x.strip().lower() for x in os.getenv("FABRIENT_STARTUP_DOMAINS", "").split(",") if x.strip()}

# Conservative defaults. Paid users receive the full authoritative registry; everyone else gets the core set.
FREE_TOOL_NAMES = {
    "inspect_part", "analyze_dfm", "verify_fixes", "validate_material", "validate_machine_envelope",
    "validate_dimension", "check_wall_thickness", "check_clearances", "check_holes", "check_overhangs",
    "check_orientation", "check_tolerances", "check_fit", "check_first_layer", "check_bed_adhesion",
    "check_revision_consistency", "compare_revisions", "trace_provenance", "build_inspection_plan",
    "estimate_risk", "next_experiment",
}

RATE_LIMIT = max(10, int(os.getenv("FABRIENT_MCP_REQUESTS_PER_MINUTE", "120")))
_WINDOW = 60.0
_buckets: dict[str, deque[float]] = defaultdict(deque)


def _segment(user: dict[str, Any]) -> tuple[str, str, str]:
    metadata = user.get("user_metadata") or {}
    app_metadata = user.get("app_metadata") or {}
    raw = str(
        metadata.get("account_type")
        or metadata.get("company_type")
        or metadata.get("organization_type")
        or metadata.get("segment")
        or app_metadata.get("account_type")
        or app_metadata.get("segment")
        or ""
    ).strip().lower()
    aliases = {"hobby": "hobbyist", "solo": "hobbyist", "individual": "hobbyist", "company": "startup"}
    raw = aliases.get(raw, raw)
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


async def _billing(user_id: str) -> dict[str, Any]:
    if not REVENUECAT_SECRET or not PROJECT_ID:
        return {"paid": None, "plan": "unknown", "source": "not_configured", "entitlements": [], "status": "unknown"}
    url = f"https://api.revenuecat.com/v2/projects/{PROJECT_ID}/customers/{user_id}/active_entitlements"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(url, params={"limit": 100}, headers={"Accept": "application/json", "Authorization": f"Bearer {REVENUECAT_SECRET}"})
        if r.status_code == 404:
            return {"paid": False, "plan": "free", "source": "revenuecat", "entitlements": [], "status": "verified"}
        if r.status_code != 200:
            return {"paid": None, "plan": "unknown", "source": "revenuecat_error", "entitlements": [], "status": "unknown", "http_status": r.status_code}
        items = (r.json() or {}).get("items") or []
        ids = sorted({str(x.get("entitlement_id")) for x in items if isinstance(x, dict) and x.get("entitlement_id")})
        paid = bool(items)
        pro = any(str(x.get("lookup_key") or x.get("display_name") or "").lower() == PRO_ENTITLEMENT for x in items if isinstance(x, dict))
        return {"paid": paid, "plan": "pro" if pro else ("paid" if paid else "free"), "source": "revenuecat", "entitlements": ids, "status": "verified"}
    except (httpx.HTTPError, ValueError):
        return {"paid": None, "plan": "unknown", "source": "revenuecat_error", "entitlements": [], "status": "unknown"}


async def _identity(request: Request) -> dict[str, Any] | None:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer ") or not SUPABASE_ANON_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(f"{ISSUER}/user", headers={"apikey": SUPABASE_ANON_KEY, "Authorization": auth})
        if r.status_code != 200:
            return None
        user = r.json()
        uid = user.get("id")
        if not uid:
            return None
        billing = await _billing(uid)
        segment, basis, confidence = _segment(user)
        return {
            "user_id": uid,
            "email": str(user.get("email") or "").lower(),
            "email_verified": bool(user.get("email_confirmed_at") or user.get("confirmed_at")),
            "name": (user.get("user_metadata") or {}).get("full_name") or (user.get("user_metadata") or {}).get("name"),
            "paid": billing["paid"],
            "plan": billing["plan"],
            "billing_status": billing["status"],
            "billing_source": billing["source"],
            "entitlements": billing["entitlements"],
            "segment": segment,
            "segment_basis": basis,
            "segment_confidence": confidence,
        }
    except (httpx.HTTPError, ValueError):
        return None


def _allowed(identity: dict[str, Any], name: str) -> bool:
    return identity.get("paid") is True or name in FREE_TOOL_NAMES


class ProductionMCPAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, registry: tuple[tuple[str, str, str], ...]):
        super().__init__(app)
        self.registry = registry

    async def dispatch(self, request: Request, call_next: Callable):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.fabrient_request_id = request_id
        path = request.url.path
        public = path in {
            "/", "/health", "/capabilities", "/account",
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-protected-resource/mcp",
            "/.well-known/oauth-authorization-server",
        }
        # Rate limit protected traffic by authenticated user where possible, otherwise by IP.
        identity = None
        if not public or path in {"/capabilities", "/account"}:
            identity = await _identity(request)
            key = f"user:{identity['user_id']}" if identity else f"ip:{request.client.host if request.client else 'unknown'}"
            now = time.monotonic()
            bucket = _buckets[key]
            while bucket and bucket[0] <= now - _WINDOW:
                bucket.popleft()
            if len(bucket) >= RATE_LIMIT:
                return JSONResponse({"error": "rate_limited", "request_id": request_id}, status_code=429, headers={"Retry-After": "60", "X-Request-ID": request_id})
            bucket.append(now)
        if path.startswith("/mcp") and identity is None:
            return JSONResponse(
                {"error": "unauthorized", "message": "A valid Fabrient OAuth access token is required.", "request_id": request_id},
                status_code=401,
                headers={"WWW-Authenticate": f'Bearer resource_metadata="{RESOURCE_METADATA}"', "X-Request-ID": request_id},
            )
        if identity is not None:
            request.state.fabrient_account = identity
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers.setdefault("Cache-Control", "no-store")
        return response


async def protected_resource(_: Request):
    return JSONResponse({
        "resource": RESOURCE,
        "authorization_servers": [ISSUER],
        "scopes_supported": ["openid", "email", "profile"],
        "bearer_methods_supported": ["header"],
    })


async def oauth_discovery(_: Request):
    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(DISCOVERY)
        r.raise_for_status()
        return JSONResponse(r.json(), headers={"Cache-Control": "no-store"})


async def health(_: Request):
    return JSONResponse({"status": "ok", "service": "fabrient-mcp", "oauth": {"issuer": ISSUER, "discovery": DISCOVERY}, "resource": RESOURCE})


def wrap_app(mcp_app: Any, registry: tuple[tuple[str, str, str], ...]) -> Starlette:
    async def capabilities(request: Request):
        identity = await _identity(request)
        if identity is None:
            return JSONResponse({"error": "unauthorized"}, status_code=401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{RESOURCE_METADATA}"'})
        available = list(registry) if identity["paid"] is True else [x for x in registry if x[0] in FREE_TOOL_NAMES]
        return JSONResponse({
            "name": "Fabrient Engineering",
            "authenticated": True,
            "account": {k: identity[k] for k in ("user_id", "email", "email_verified", "paid", "plan", "billing_status", "entitlements", "segment", "segment_basis", "segment_confidence")},
            "tool_count": len(available),
            "total_tool_count": len(registry),
            "tools": [x[0] for x in available],
            "gated_tool_count": len(registry) - len(available),
            "access_policy": "free_core_plus_paid_advanced_tools",
        })

    async def account(request: Request):
        identity = await _identity(request)
        if identity is None:
            return JSONResponse({"error": "unauthorized"}, status_code=401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{RESOURCE_METADATA}"'})
        return JSONResponse({"account": identity})

    wrapper = Starlette(routes=[
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

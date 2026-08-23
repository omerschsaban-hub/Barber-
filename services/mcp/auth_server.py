from __future__ import annotations

import html
import os
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Mount, Route

from server import CAPABILITY_REGISTRY, app as mcp_app

PROJECT_ID = os.getenv("REVENUECAT_PROJECT_ID", "projb138a8db")
PRO_ENTITLEMENT = os.getenv("FABRIENT_PRO_ENTITLEMENT", "create_an_app_called_fabrinat_pro")
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "https://gphmefejeqvlemzvmade.supabase.co").rstrip("/")
SUPABASE_AUTH_ISSUER = f"{SUPABASE_URL}/auth/v1"
SUPABASE_OAUTH_DISCOVERY = f"{SUPABASE_URL}/.well-known/oauth-authorization-server/auth/v1"
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
MCP_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "fabrient-mcp.onrender.com")
MCP_RESOURCE_URL = os.getenv("FABRIENT_MCP_RESOURCE_URL", f"https://{MCP_HOST}/mcp").rstrip("/")
MCP_RESOURCE_METADATA_URL = f"https://{MCP_HOST}/.well-known/oauth-protected-resource"
# Fabrient authentication is email-code only. There is intentionally no Google OAuth/provider button.
OAUTH_SCOPES = ["openid", "email"]
PUBLIC_EMAIL_DOMAINS = {"gmail.com", "googlemail.com", "outlook.com", "hotmail.com", "live.com", "yahoo.com", "icloud.com", "proton.me", "protonmail.com"}
ENTERPRISE_DOMAINS = {x.strip().lower() for x in os.getenv("FABRIENT_ENTERPRISE_DOMAINS", "").split(",") if x.strip()}
STARTUP_DOMAINS = {x.strip().lower() for x in os.getenv("FABRIENT_STARTUP_DOMAINS", "").split(",") if x.strip()}

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


async def _authenticated_user(request: Request) -> dict[str, Any] | None:
    authorization = request.headers.get("authorization")
    revenuecat_secret = os.getenv("REVENUECAT_SECRET_API_KEY") or os.getenv("REVENUECAT_API_KEY")
    if not authorization or not authorization.lower().startswith("bearer ") or not SUPABASE_ANON_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            user_response = await client.get(
                f"{SUPABASE_AUTH_ISSUER}/user",
                headers={"apikey": SUPABASE_ANON_KEY, "Authorization": authorization},
            )
            if user_response.status_code != 200:
                return None
            user = user_response.json()
            user_id = user.get("id")
            if not user_id:
                return None
            email = str(user.get("email") or "").lower()
            metadata = user.get("user_metadata") or {}
            app_metadata = user.get("app_metadata") or {}
            domain = email.rsplit("@", 1)[-1] if "@" in email else ""
            billing = {"paid": None, "plan": "unknown", "source": "not_configured", "entitlements": []}
            if revenuecat_secret and PROJECT_ID:
                entitlement_response = await client.get(
                    f"https://api.revenuecat.com/v2/projects/{PROJECT_ID}/customers/{user_id}/active_entitlements",
                    headers={"Accept": "application/json", "Authorization": f"Bearer {revenuecat_secret}"},
                )
                if entitlement_response.status_code == 200:
                    items = (entitlement_response.json() or {}).get("items", [])
                    entitlement_ids = {str(i.get("entitlement_id")) for i in items if isinstance(i, dict) and i.get("entitlement_id")}
                    entitlement_names = {str(i.get("lookup_key") or i.get("display_name") or i.get("id") or "").lower() for i in items if isinstance(i, dict)}
                    pro = PRO_ENTITLEMENT.lower() in entitlement_names
                    billing = {"paid": bool(items), "plan": "pro" if pro else ("paid" if items else "free"), "source": "revenuecat", "entitlements": sorted(x for x in entitlement_names if x), "entitlement_ids": sorted(x for x in entitlement_ids if x)}
            explicit_segment = str(metadata.get("account_type") or metadata.get("company_type") or metadata.get("organization_type") or app_metadata.get("account_type") or "").lower()
            if explicit_segment in {"enterprise", "startup", "hobbyist"}:
                segment, basis, confidence = explicit_segment, "explicit_account_metadata", "high"
            elif domain in ENTERPRISE_DOMAINS:
                segment, basis, confidence = "enterprise", "configured_enterprise_domain", "high"
            elif domain in STARTUP_DOMAINS:
                segment, basis, confidence = "startup", "configured_startup_domain", "high"
            elif domain in PUBLIC_EMAIL_DOMAINS:
                segment, basis, confidence = "hobbyist", "consumer_email_domain", "medium"
            elif domain:
                segment, basis, confidence = "startup", "custom_domain_default", "low"
            else:
                segment, basis, confidence = "unknown", "insufficient_identity_data", "low"
            return {"user_id": user_id, "email": email, "email_verified": bool(user.get("email_confirmed_at") or user.get("confirmed_at")), "name": metadata.get("full_name") or metadata.get("name"), "paid": billing["paid"], "plan": billing["plan"], "entitlements": billing["entitlements"], "billing_source": billing["source"], "segment": segment, "segment_basis": basis, "segment_confidence": confidence}
    except (httpx.HTTPError, ValueError):
        return None


async def capabilities(request: Request) -> JSONResponse:
    identity = await _authenticated_user(request)
    if identity is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{MCP_RESOURCE_METADATA_URL}"'})
    available = list(CAPABILITY_REGISTRY) if identity["paid"] else [item for item in CAPABILITY_REGISTRY if item[0] in FREE_TOOL_NAMES]
    return JSONResponse({"name": "Fabrient Engineering", "authenticated": True, "account": {k: identity[k] for k in ("user_id", "email", "paid", "plan", "entitlements", "segment", "segment_basis", "segment_confidence")}, "tool_count": len(available), "total_tool_count": len(CAPABILITY_REGISTRY), "tools": [name for name, _, _ in available], "gated_tool_count": len(CAPABILITY_REGISTRY) - len(available), "registry_authoritative": True, "access_policy": "free_core_plus_paid_advanced_tools", "oauth": {"issuer": SUPABASE_AUTH_ISSUER, "discovery": SUPABASE_OAUTH_DISCOVERY, "resource": MCP_RESOURCE_URL, "scopes": OAUTH_SCOPES, "login_method": "email_otp"}})


async def account(request: Request) -> JSONResponse:
    identity = await _authenticated_user(request)
    if identity is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{MCP_RESOURCE_METADATA_URL}"'})
    return JSONResponse({"account": identity})


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "fabrient-mcp-auth-wrapper", "tool_count": len(CAPABILITY_REGISTRY), "oauth_discovery": SUPABASE_OAUTH_DISCOVERY, "login_method": "email_otp", "google_oauth": False})


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
    """Send a Supabase email OTP. No Google provider is involved."""
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
        return JSONResponse({"ok": True, "message": "Code sent. Check your email.", "open_gmail_url": "https://mail.google.com/"})
    except (ValueError, httpx.HTTPError):
        return JSONResponse({"error": "We couldn't send the code. Please try again."}, status_code=400)


async def login(request: Request) -> HTMLResponse:
    next_url = html.escape(request.query_params.get("next", "/"), quote=True)
    return HTMLResponse(f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Fabrient — Sign in</title><style>body{{font-family:system-ui,-apple-system,sans-serif;background:#0b0d10;color:#f4f5f7;display:grid;place-items:center;min-height:100vh;margin:0}}main{{width:min(420px,calc(100% - 40px));padding:32px;border:1px solid #272b33;border-radius:18px;background:#11141a}}h1{{margin:0 0 8px}}p{{color:#a8afbb;line-height:1.5}}input{{box-sizing:border-box;width:100%;padding:13px 14px;border-radius:10px;border:1px solid #363c46;background:#0c0f14;color:white;margin:10px 0 12px}}button,a{{display:block;width:100%;box-sizing:border-box;text-align:center;padding:13px;border-radius:10px;border:0;font-weight:650;text-decoration:none;cursor:pointer}}button{{background:#fff;color:#0b0d10}}a{{margin-top:10px;background:#242a33;color:white}}small{{display:block;color:#737b88;margin-top:14px}}#status{{margin-top:12px}}</style></head><body><main><h1>Sign in to Fabrient</h1><p>Enter your email and we'll send you a one-time code. No Google sign-in.</p><form id='f'><input id='email' type='email' autocomplete='email' placeholder='you@example.com' required><button type='submit'>Email me a code</button></form><a id='gmail' href='https://mail.google.com/' target='_blank' rel='noopener' style='display:none'>Open Gmail</a><div id='status'></div><small>Use the code in the authorization window after checking your inbox.</small></main><script>const f=document.getElementById('f'),s=document.getElementById('status'),g=document.getElementById('gmail');f.addEventListener('submit',async e=>{{e.preventDefault();s.textContent='Sending…';g.style.display='none';try{{const r=await fetch('/request-code',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:document.getElementById('email').value}})}});const d=await r.json();if(!r.ok)throw new Error(d.error||'Could not send code');s.textContent='Code sent. Check your inbox.';g.style.display='block';}}catch(err){{s.textContent=err.message}}}});</script></body></html>""")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        public = {"/health", "/", "/capabilities", "/account", "/login", "/request-code", "/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp", "/.well-known/oauth-authorization-server"}
        if request.url.path in public:
            return await call_next(request)
        if request.url.path.startswith("/mcp"):
            identity = await _authenticated_user(request)
            if identity is None:
                return JSONResponse({"error": "Unauthorized", "message": "A valid Supabase email-code access token is required."}, status_code=401, headers={"WWW-Authenticate": f'Bearer resource_metadata="{MCP_RESOURCE_METADATA_URL}"'})
            request.state.fabrient_account = identity
        return await call_next(request)


app = Starlette(routes=[Route("/health", health, methods=["GET"]), Route("/capabilities", capabilities, methods=["GET"]), Route("/account", account, methods=["GET"]), Route("/login", login, methods=["GET"]), Route("/request-code", request_code, methods=["POST"]), Route("/.well-known/oauth-protected-resource", protected_resource, methods=["GET"]), Route("/.well-known/oauth-protected-resource/mcp", protected_resource, methods=["GET"]), Route("/.well-known/oauth-authorization-server", oauth_discovery, methods=["GET"]), Mount("/", app=mcp_app)])
app.add_middleware(AuthMiddleware)

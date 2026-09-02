from __future__ import annotations
import base64, hashlib, hmac, os, secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from urllib.parse import urlencode, parse_qs
from typing import Any
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Mount, Route
try:
    from .migrate import main as _apply_owned_schema
except ImportError:
    from migrate import main as _apply_owned_schema
# MCP requires the shared PostgreSQL database. Do not silently skip schema
# verification when DATABASE_URL is missing; a green health endpoint with an
# unverified database is worse than a failed deployment.
_apply_owned_schema()
try:
    from .server import CAPABILITY_REGISTRY, app as mcp_app
    from .auth_db import user_from_bearer, _pool, _hash
except ImportError:
    from server import CAPABILITY_REGISTRY, app as mcp_app
    from auth_db import user_from_bearer, _pool, _hash

MCP_HOST = os.getenv('RENDER_EXTERNAL_HOSTNAME', 'fabrient-mcp.onrender.com')
RESOURCE = os.getenv('FABRIENT_MCP_RESOURCE_URL', f'https://{MCP_HOST}/mcp').rstrip('/')
ISSUER = os.getenv('FABRIENT_MCP_OAUTH_ISSUER', f'https://{MCP_HOST}').rstrip('/')
SCOPES = {'openid', 'email', 'profile', 'mcp:use'}
FREE = {'inspect_part','analyze_dfm','verify_fixes','validate_material','validate_machine_envelope','validate_dimension','check_wall_thickness','check_clearances','check_holes','check_overhangs','check_orientation','check_tolerances','check_fit','check_first_layer','check_bed_adhesion','check_revision_consistency','compare_revisions','trace_provenance','build_inspection_plan','estimate_risk','next_experiment'}
if len(CAPABILITY_REGISTRY) != 100 or len({x[0] for x in CAPABILITY_REGISTRY}) != 100:
    raise RuntimeError('MCP registry must contain exactly 100 unique tools')

def digest(v: str) -> bytes:
    return hashlib.sha256(v.encode()).digest()

def pkce(v: str) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).decode().rstrip('=')

def client(cid: str):
    with _pool().connection() as c:
        return c.execute('select client_id,client_name,redirect_uris,client_secret_hash,public_client from oauth_clients where client_id=%s', (cid,)).fetchone()

def user(req: Request) -> dict[str, Any] | None:
    a = req.headers.get('authorization', '')
    return user_from_bearer(a[7:].strip()) if a.lower().startswith('bearer ') else None

def has_scope(identity: dict[str, Any] | None, required: str) -> bool:
    return bool(identity and required in set(str(identity.get('scope') or '').split()))

PLAN_ORDER = ('free', 'hobbyist', 'startup', 'enterprise')
LEGACY_PRO_ENTITLEMENT = 'create_an_app_called_fabrinat_pro'

def _csv(name: str) -> set[str]:
    return {item.strip() for item in os.getenv(name, '').split(',') if item.strip()}

def plan_for_user(uid: str) -> str:
    with _pool().connection() as c:
        rows = c.execute("select entitlement_id, product_id from billing_entitlements where user_id=%s and active=true and (expires_at is null or expires_at>now())", (uid,)).fetchall()
    for plan in reversed(PLAN_ORDER[1:]):
        entitlement_ids = _csv(f'FABRIENT_{plan.upper()}_ENTITLEMENTS')
        product_ids = _csv(f'FABRIENT_{plan.upper()}_PRODUCT_IDS')
        if plan == 'hobbyist':
            entitlement_ids.update({'fabrinat_hobby', LEGACY_PRO_ENTITLEMENT})
        if any(row['entitlement_id'] in entitlement_ids or row['product_id'] in product_ids for row in rows):
            return plan
    return 'free'

def form_body(raw: bytes) -> dict[str, str]:
    parsed = parse_qs(raw.decode('utf-8'), keep_blank_values=True)
    return {k: v[-1] for k, v in parsed.items()}

def _valid_redirect(uri: str) -> bool:
    return uri.startswith('https://') or uri.startswith('http://localhost') or uri.startswith('http://127.0.0.1') or uri.startswith('http://[::1]')

async def health(_: Request):
    return JSONResponse({'status': 'ok', 'service': 'fabrient-mcp-auth-wrapper', 'tool_count': 100})

async def caps(r: Request):
    u = user(r)
    if not u:

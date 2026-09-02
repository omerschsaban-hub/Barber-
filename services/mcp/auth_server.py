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
    try:
        with _pool().connection() as db:
            row = db.execute("SELECT COUNT(*) AS count FROM schema_migrations WHERE checksum IS NOT NULL").fetchone()
            checksum_count = int(row['count'] if isinstance(row, dict) else row[0])
        if checksum_count < 1:
            raise RuntimeError('schema migration ledger is not initialized')
        return JSONResponse({'status': 'ok', 'service': 'fabrient-mcp-auth-wrapper', 'tool_count': 100, 'database': 'ok', 'migration_checksums': checksum_count})
    except Exception as exc:
        return JSONResponse({'status': 'degraded', 'service': 'fabrient-mcp-auth-wrapper', 'database': 'error', 'error': str(exc)}, 503)

async def caps(r: Request):
    u = user(r)
    if not u:
        return JSONResponse({'error': 'Unauthorized'}, 401, headers={'WWW-Authenticate': f'Bearer resource_metadata="{ISSUER}/.well-known/oauth-protected-resource/mcp", scope="mcp:use"'})
    plan = plan_for_user(u['user_id'])
    tools = list(CAPABILITY_REGISTRY) if plan in {'startup', 'enterprise'} else [x for x in CAPABILITY_REGISTRY if x[0] in FREE]
    return JSONResponse({'name': 'Fabrient Engineering', 'authenticated': True, 'plan': plan, 'pro': plan != 'free', 'tool_count': len(tools), 'total_tool_count': 100, 'tools': [x[0] for x in tools], 'gated_tool_count': 100-len(tools), 'registry_authoritative': True})

async def protected(_: Request):
    return JSONResponse({'resource': RESOURCE, 'authorization_servers': [ISSUER], 'scopes_supported': sorted(SCOPES), 'bearer_methods_supported': ['header']})

async def metadata(_: Request):
    return JSONResponse({'issuer': ISSUER, 'authorization_endpoint': f'{ISSUER}/oauth/authorize', 'token_endpoint': f'{ISSUER}/oauth/token', 'registration_endpoint': f'{ISSUER}/oauth/register', 'revocation_endpoint': f'{ISSUER}/oauth/revoke', 'response_types_supported': ['code'], 'grant_types_supported': ['authorization_code'], 'token_endpoint_auth_methods_supported': ['none'], 'code_challenge_methods_supported': ['S256'], 'scopes_supported': sorted(SCOPES), 'client_id_metadata_document_supported': False})

async def register(r: Request):
    try:
        payload = await r.json()
    except Exception:
        return JSONResponse({'error': 'invalid_client_metadata'}, 400)
    redirect_uris = payload.get('redirect_uris')
    if not isinstance(redirect_uris, list) or not redirect_uris or not all(isinstance(x, str) and _valid_redirect(x) for x in redirect_uris):
        return JSONResponse({'error': 'invalid_redirect_uri', 'error_description': 'redirect_uris must contain HTTPS or loopback redirect URIs'}, 400)
    grant_types = payload.get('grant_types') or ['authorization_code']
    response_types = payload.get('response_types') or ['code']
    if 'authorization_code' not in grant_types or 'code' not in response_types:
        return JSONResponse({'error': 'invalid_client_metadata', 'error_description': 'Only authorization_code/code is supported'}, 400)
    auth_method = payload.get('token_endpoint_auth_method', 'none')
    if auth_method != 'none':
        return JSONResponse({'error': 'invalid_client_metadata', 'error_description': 'Fabrient MCP uses public OAuth clients with PKCE'}, 400)
    client_id = 'fabrient_' + secrets.token_urlsafe(24)
    client_name = str(payload.get('client_name') or 'MCP client')[:200]
    with _pool().connection() as db:
        db.execute('insert into oauth_clients(client_id,client_name,redirect_uris,client_secret_hash,public_client) values(%s,%s,%s,NULL,TRUE)', (client_id, client_name, redirect_uris))
    return JSONResponse({'client_id': client_id, 'client_name': client_name, 'redirect_uris': redirect_uris, 'grant_types': ['authorization_code'], 'response_types': ['code'], 'token_endpoint_auth_method': 'none'}, 201)

async def authorize(r: Request):
    q = r.query_params
    cid, ru, rt = q.get('client_id',''), q.get('redirect_uri',''), q.get('response_type')
    scope, state, ch, cm = q.get('scope','openid email'), q.get('state'), q.get('code_challenge'), q.get('code_challenge_method')
    c = client(cid)
    if not c or rt != 'code' or ru not in (c['redirect_uris'] or []):
        return JSONResponse({'error': 'invalid_request'}, 400)
    requested = set(scope.split())
    if not requested.issubset(SCOPES):
        return JSONResponse({'error': 'invalid_scope'}, 400)
    if ch and cm != 'S256':
        return JSONResponse({'error': 'invalid_request', 'error_description': 'Only S256 PKCE is supported'}, 400)
    if c['public_client'] and not ch:
        return JSONResponse({'error': 'invalid_request', 'error_description': 'PKCE is required for public clients'}, 400)
    with _pool().connection() as db:
        row = db.execute("insert into oauth_authorization_requests(client_id,redirect_uri,scope,state,code_challenge,code_challenge_method,expires_at) values(%s,%s,%s,%s,%s,%s,now()+interval '10 minutes') returning id", (cid, ru, ' '.join(sorted(requested)), state, ch, cm)).fetchone()
    return RedirectResponse(f"{os.getenv('FABRIENT_WEB_ORIGIN','https://fabrient.com').rstrip('/')}/oauth/consent?authorization_id={row['id']}", 302)

async def details(r: Request):
    with _pool().connection() as db:
        row = db.execute("select r.id,r.client_id,c.client_name,r.redirect_uri,r.scope,r.state,r.expires_at,r.approved_at,r.denied_at from oauth_authorization_requests r join oauth_clients c on c.client_id=r.client_id where r.id=%s", (r.path_params['id'],)).fetchone()
    if not row or row['expires_at'] <= datetime.now(timezone.utc) or row['approved_at'] or row['denied_at']:
        return JSONResponse({'error': 'invalid_request'}, 400)
    return JSONResponse({'authorization_id': str(row['id']), 'client': {'client_id': row['client_id'], 'name': row['client_name']}, 'redirect_uri': row['redirect_uri'], 'scope': row['scope']})

async def decide(r: Request):

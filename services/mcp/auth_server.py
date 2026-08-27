from __future__ import annotations
import base64, hashlib, hmac, os, secrets
from datetime import datetime, timezone
from urllib.parse import urlencode, parse_qs
from typing import Any
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse
from starlette.routing import Mount, Route
try:
    from server import CAPABILITY_REGISTRY, app as mcp_app
    from auth_db import user_from_bearer, _pool, _hash
except ModuleNotFoundError:
    from .server import CAPABILITY_REGISTRY, app as mcp_app
    from .auth_db import user_from_bearer, _pool, _hash

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

async def health(_: Request):
    return JSONResponse({'status': 'ok', 'service': 'fabrient-mcp-auth-wrapper', 'tool_count': 100})

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
    return JSONResponse({'issuer': ISSUER, 'authorization_endpoint': f'{ISSUER}/oauth/authorize', 'token_endpoint': f'{ISSUER}/oauth/token', 'revocation_endpoint': f'{ISSUER}/oauth/revoke', 'response_types_supported': ['code'], 'grant_types_supported': ['authorization_code'], 'code_challenge_methods_supported': ['S256'], 'scopes_supported': sorted(SCOPES)})

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
    u = user(r)
    if not u:
        return JSONResponse({'error': 'Unauthorized'}, 401)
    rid, decision = r.path_params['id'], r.path_params['decision']
    if decision not in {'approve', 'deny'}:
        return JSONResponse({'error': 'invalid_request'}, 400)
    with _pool().connection() as db:
        with db.transaction():
            row = db.execute('select * from oauth_authorization_requests where id=%s for update', (rid,)).fetchone()
            if not row or row['expires_at'] <= datetime.now(timezone.utc) or row['approved_at'] or row['denied_at']:
                return JSONResponse({'error': 'invalid_request'}, 400)
            if decision == 'deny':
                db.execute('update oauth_authorization_requests set denied_at=now(),user_id=%s where id=%s', (u['user_id'], rid))
                target = row['redirect_uri'] + ('&' if '?' in row['redirect_uri'] else '?') + urlencode({'error': 'access_denied', 'state': row['state'] or ''})
                return JSONResponse({'redirect_url': target})
            code = secrets.token_urlsafe(48)
            db.execute("insert into oauth_authorization_codes(code_hash,client_id,user_id,redirect_uri,code_challenge,code_challenge_method,scope,expires_at) values(%s,%s,%s,%s,%s,%s,%s,now()+interval '60 seconds')", (digest(code), row['client_id'], u['user_id'], row['redirect_uri'], row['code_challenge'], row['code_challenge_method'], row['scope']))
            db.execute('update oauth_authorization_requests set approved_at=now(),user_id=%s where id=%s', (u['user_id'], rid))
            target = row['redirect_uri'] + ('&' if '?' in row['redirect_uri'] else '?') + urlencode({'code': code, 'state': row['state'] or ''})
            return JSONResponse({'redirect_url': target})

async def token(r: Request):
    f = form_body(await r.body())
    cid, code, ru, ver = f.get('client_id',''), f.get('code',''), f.get('redirect_uri',''), f.get('code_verifier','')
    if f.get('grant_type') != 'authorization_code' or not cid or not code or not ru:
        return JSONResponse({'error': 'invalid_request'}, 400)
    c = client(cid)
    if not c:
        return JSONResponse({'error': 'invalid_client'}, 401)
    with _pool().connection() as db:
        with db.transaction():
            row = db.execute('select * from oauth_authorization_codes where code_hash=%s and client_id=%s for update', (digest(code), cid)).fetchone()
            if not row or row['consumed_at'] or row['expires_at'] <= datetime.now(timezone.utc) or row['redirect_uri'] != ru:
                return JSONResponse({'error': 'invalid_grant'}, 400)
            if row['code_challenge'] and (not ver or not hmac.compare_digest(pkce(ver), row['code_challenge'])):
                return JSONResponse({'error': 'invalid_grant'}, 400)
            if not c['public_client']:
                secret = f.get('client_secret','')
                stored = bytes(c['client_secret_hash'] or b'')
                if not secret or not hmac.compare_digest(digest(secret), stored):
                    return JSONResponse({'error': 'invalid_client'}, 401)
            tok = secrets.token_urlsafe(48)
            db.execute('update oauth_authorization_codes set consumed_at=now() where code_hash=%s', (digest(code),))
            db.execute("insert into oauth_access_tokens(token_hash,client_id,user_id,scope,expires_at) values(%s,%s,%s,%s,now()+interval '1 hour')", (_hash(tok), cid, row['user_id'], row['scope']))
            return JSONResponse({'access_token': tok, 'token_type': 'Bearer', 'expires_in': 3600, 'scope': row['scope']})

async def revoke(r: Request):
    f = form_body(await r.body())
    t = f.get('token','')
    if t:
        with _pool().connection() as db:
            db.execute('update oauth_access_tokens set revoked_at=now() where token_hash=%s', (_hash(t),))
    return JSONResponse({})

class Auth(BaseHTTPMiddleware):
    async def dispatch(self, r, call_next):
        public = {'/', '/health', '/.well-known/oauth-protected-resource', '/.well-known/oauth-protected-resource/mcp', '/.well-known/oauth-authorization-server', '/oauth/authorize', '/oauth/token', '/oauth/revoke'}
        if r.url.path in public or r.url.path.startswith('/oauth/details/') or r.url.path.startswith('/oauth/decide/') or r.url.path == '/capabilities':
            return await call_next(r)
        if r.url.path.startswith('/mcp'):
            identity = user(r)
            if not identity:
                return JSONResponse({'error': 'Unauthorized'}, 401, headers={'WWW-Authenticate': f'Bearer resource_metadata="{ISSUER}/.well-known/oauth-protected-resource/mcp", scope="mcp:use"'})
            if not has_scope(identity, 'mcp:use'):
                return JSONResponse({'error': 'insufficient_scope'}, 403, headers={'WWW-Authenticate': 'Bearer error="insufficient_scope", scope="mcp:use"'})
        return await call_next(r)

routes = [Route('/', health), Route('/health', health), Route('/capabilities', caps), Route('/.well-known/oauth-protected-resource', protected), Route('/.well-known/oauth-protected-resource/mcp', protected), Route('/.well-known/oauth-authorization-server', metadata), Route('/oauth/authorize', authorize), Route('/oauth/token', token, methods=['POST']), Route('/oauth/revoke', revoke, methods=['POST']), Route('/oauth/details/{id}', details), Route('/oauth/decide/{id}/{decision}', decide, methods=['POST']), Mount('/', app=mcp_app)]
app = Starlette(routes=routes)
app.add_middleware(Auth)

from __future__ import annotations

import os
from typing import Any

import httpx
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from server import CAPABILITY_REGISTRY, app as mcp_app

PROJECT_ID = 'projb138a8db'
PRO_ENTITLEMENT = 'create_an_app_called_fabrinat_pro'

# Core MCP tools stay available to authenticated free users. The advanced set is
# only advertised to users whose RevenueCat entitlement is active.
FREE_TOOL_NAMES = {
    'inspect_part', 'analyze_dfm', 'verify_fixes', 'validate_material',
    'validate_machine_envelope', 'validate_dimension', 'check_wall_thickness',
    'check_clearances', 'check_holes', 'check_overhangs', 'check_orientation',
    'check_tolerances', 'check_fit', 'check_first_layer', 'check_bed_adhesion',
    'check_revision_consistency', 'compare_revisions', 'trace_provenance',
    'build_inspection_plan', 'estimate_risk', 'next_experiment',
}

TOOL_BY_NAME = {name: (description, path) for name, description, path in CAPABILITY_REGISTRY}
if not FREE_TOOL_NAMES.issubset(TOOL_BY_NAME):
    raise RuntimeError('Free MCP tool allowlist contains an unknown tool')

async def _authenticated_user(request: Request) -> dict[str, Any] | None:
    authorization = request.headers.get('authorization')
    supabase_url = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
    supabase_anon_key = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    revenuecat_secret = os.getenv('REVENUECAT_SECRET_API_KEY')
    if not authorization or not authorization.startswith('Bearer '):
        return None
    if not supabase_url or not supabase_anon_key or not revenuecat_secret:
        return None

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            user_response = await client.get(
                f'{supabase_url.rstrip("/")}/auth/v1/user',
                headers={'apikey': supabase_anon_key, 'Authorization': authorization},
            )
            if user_response.status_code != 200:
                return None
            user = user_response.json()
            user_id = user.get('id')
            if not user_id:
                return None

            entitlement_response = await client.get(
                f'https://api.revenuecat.com/v2/projects/{PROJECT_ID}/customers/{user_id}/active_entitlements',
                headers={'Accept': 'application/json', 'Authorization': f'Bearer {revenuecat_secret}'},
            )
            if entitlement_response.status_code != 200:
                return None
            body = entitlement_response.json()
            items = body.get('items', []) if isinstance(body, dict) else []
            active_ids = {
                str(item.get('entitlement_id'))
                for item in items if isinstance(item, dict) and item.get('entitlement_id')
            }
            # RevenueCat v2 active_entitlements returns entitlement_id; resolve it
            # against the project entitlement catalog before comparing the stable lookup key.
            pro = False
            if active_ids:
                catalog = await client.get(
                    f'https://api.revenuecat.com/v2/projects/{PROJECT_ID}/entitlements',
                    params={'limit': 100},
                    headers={'Accept': 'application/json', 'Authorization': f'Bearer {revenuecat_secret}'},
                )
                if catalog.status_code != 200:
                    return None
                catalog_items = (catalog.json() or {}).get('items', [])
                pro = any(
                    str(item.get('id')) in active_ids and item.get('lookup_key') == PRO_ENTITLEMENT
                    for item in catalog_items if isinstance(item, dict)
                )
            return {'user_id': user_id, 'pro': pro}
    except (httpx.HTTPError, ValueError):
        return None

async def capabilities(request: Request) -> JSONResponse:
    identity = await _authenticated_user(request)
    if identity is None:
        return JSONResponse({'error': 'Unauthorized'}, status_code=401)

    available = list(CAPABILITY_REGISTRY) if identity['pro'] else [
        item for item in CAPABILITY_REGISTRY if item[0] in FREE_TOOL_NAMES
    ]
    return JSONResponse({
        'name': 'Fabrient Engineering',
        'authenticated': True,
        'pro': identity['pro'],
        'entitlement': PRO_ENTITLEMENT,
        'tool_count': len(available),
        'total_tool_count': len(CAPABILITY_REGISTRY),
        'tools': [name for name, _, _ in available],
        'gated_tool_count': len(CAPABILITY_REGISTRY) - len(available),
        'registry_authoritative': True,
        'access_policy': 'free_core_plus_pro_advanced_tools',
    })

async def health(_: Request) -> JSONResponse:
    return JSONResponse({'status': 'ok', 'service': 'fabrient-mcp-auth-wrapper', 'tool_count': len(CAPABILITY_REGISTRY)})

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Health remains public for deployment checks. MCP traffic and capability
        # discovery require a real Supabase user token.
        if request.url.path in {'/health', '/'}:
            return await call_next(request)
        if request.url.path == '/capabilities':
            return await call_next(request)
        if request.url.path.startswith('/mcp'):
            identity = await _authenticated_user(request)
            if identity is None:
                return JSONResponse({'error': 'Unauthorized', 'message': 'A valid Supabase access token is required.'}, status_code=401)
        return await call_next(request)

app = Starlette(
    routes=[
        Route('/health', health, methods=['GET']),
        Route('/capabilities', capabilities, methods=['GET']),
        Mount('/', app=mcp_app),
    ],
)
app.add_middleware(AuthMiddleware)

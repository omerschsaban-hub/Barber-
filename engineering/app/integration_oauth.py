from __future__ import annotations
import base64, hashlib, os, secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException
from .auth_db import _pool, user_from_bearer
from .mcp_integrations import MCP_PROVIDERS

PUBLIC_WEB_URL = os.getenv("FABRIENT_WEB_URL", os.getenv("NEXT_PUBLIC_FABRIENT_WEB_URL", "https://fabrinat-omega.vercel.app")).rstrip("/")
REDIRECT_URI = os.getenv("FABRIENT_INTEGRATION_OAUTH_REDIRECT", f"{PUBLIC_WEB_URL}/integrations/oauth/callback")
MASTER_KEY=os.getenv("FABRIENT_INTEGRATION_ENCRYPTION_KEY","")

def _key()->bytes:
    if not MASTER_KEY: raise RuntimeError("FABRIENT_INTEGRATION_ENCRYPTION_KEY must be configured")
    try:key=base64.urlsafe_b64decode(MASTER_KEY+"="*(-len(MASTER_KEY)%4))
    except Exception as exc: raise RuntimeError("FABRIENT_INTEGRATION_ENCRYPTION_KEY must be URL-safe base64") from exc
    if len(key)!=32: raise RuntimeError("FABRIENT_INTEGRATION_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key

def _seal(value:str)->bytes:
    nonce=secrets.token_bytes(12);return nonce+AESGCM(_key()).encrypt(nonce,value.encode(),None)

def _open(value:bytes)->str:
    nonce,ciphertext=value[:12],value[12:];return AESGCM(_key()).decrypt(nonce,ciphertext,None).decode()

def _pkce()->tuple[str,str]:
    verifier=secrets.token_urlsafe(64);challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=');return verifier,challenge

def _metadata(endpoint:str)->dict:
    base=endpoint.split('/mcp',1)[0].rstrip('/');last=None
    for url in (f'{base}/.well-known/oauth-authorization-server',f'{base}/.well-known/oauth-protected-resource/mcp'):
        try:
            r=httpx.get(url,timeout=10,follow_redirects=False);r.raise_for_status();data=r.json()
            if data.get('authorization_endpoint') and data.get('token_endpoint'): return data
            if data.get('authorization_servers'):
                rr=httpx.get(f"{data['authorization_servers'][0].rstrip('/')}/.well-known/oauth-authorization-server",timeout=10);rr.raise_for_status();return rr.json()
        except Exception as exc:last=exc
    raise RuntimeError(f'Provider OAuth metadata unavailable: {last}')

def current_user(authorization:str|None)->dict:
    token=authorization[7:].strip() if authorization and authorization.lower().startswith('bearer ') else None;identity=user_from_bearer(token)
    if not identity: raise HTTPException(status_code=401,detail='Authentication required')
    return identity

def start(provider:str,authorization:str|None)->dict:
    p=MCP_PROVIDERS.get(provider)
    if not p: raise HTTPException(status_code=404,detail='Unsupported integration')
    if p['auth']=='public': return {'provider':provider,'mode':'public','connected':True,'auth_url':p['endpoint']}
    user=current_user(authorization)
    try:metadata=_metadata(p['endpoint'])
    except Exception as exc:raise HTTPException(status_code=502,detail=str(exc))
    verifier,challenge=_pkce();state=secrets.token_urlsafe(48);client_id=os.getenv('FABRIENT_INTEGRATION_CLIENT_ID')
    with _pool().connection() as db: db.execute('INSERT INTO integration_oauth_states(state_hash,user_id,provider,code_verifier_ciphertext,redirect_uri,client_id,expires_at) VALUES(%s,%s,%s,%s,%s,%s,now()+interval \'10 minutes\')',(hashlib.sha256(state.encode()).digest(),user['user_id'],provider,_seal(verifier),REDIRECT_URI,client_id))
    if not client_id:
        reg=metadata.get('registration_endpoint')
        if not reg: raise HTTPException(status_code=503,detail='This provider requires Fabrient OAuth client configuration. Users do not need to provide credentials.')
        payload={'client_name':'Fabrient','redirect_uris':[REDIRECT_URI],'grant_types':['authorization_code'],'response_types':['code'],'token_endpoint_auth_method':'none'}
        rr=httpx.post(reg,json=payload,timeout=10,follow_redirects=False);rr.raise_for_status();client_id=rr.json().get('client_id')
        if not client_id: raise HTTPException(status_code=502,detail='Provider did not return a client_id')
        with _pool().connection() as db:db.execute('UPDATE integration_oauth_states SET client_id=%s WHERE state_hash=%s',(client_id,hashlib.sha256(state.encode()).digest()))
    params={'response_type':'code','client_id':client_id,'redirect_uri':REDIRECT_URI,'state':state,'code_challenge':challenge,'code_challenge_method':'S256'}
    scopes=metadata.get('scopes_supported') or []
    if scopes:params['scope']=' '.join(scopes)
    return {'provider':provider,'auth_url':f"{metadata['authorization_endpoint']}?{urlencode(params)}",'expires_in':600,'public_web_url':PUBLIC_WEB_URL}

def complete(code:str,state:str)->dict:
    if not code or not state:raise HTTPException(status_code=400,detail='code and state are required')
    state_hash=hashlib.sha256(state.encode()).digest()
    with _pool().connection() as db:
        row=db.execute('SELECT * FROM integration_oauth_states WHERE state_hash=%s FOR UPDATE',(state_hash,)).fetchone()
        if not row or row['consumed_at'] or row['expires_at']<=datetime.now(timezone.utc):raise HTTPException(status_code=400,detail='Invalid or expired authorization state')
        metadata=_metadata(MCP_PROVIDERS[row['provider']]['endpoint']);payload={'grant_type':'authorization_code','code':code,'redirect_uri':row['redirect_uri'],'client_id':row['client_id'],'code_verifier':_open(row['code_verifier_ciphertext'])}
        secret=os.getenv('FABRIENT_INTEGRATION_CLIENT_SECRET')
        if secret:payload['client_secret']=secret
        response=httpx.post(metadata['token_endpoint'],data=payload,timeout=15,follow_redirects=False)
        if response.status_code>=400:raise HTTPException(status_code=502,detail='Provider token exchange failed')
        token=response.json();access=token.get('access_token')
        if not access:raise HTTPException(status_code=502,detail='Provider did not return an access token')
        refresh=token.get('refresh_token');scopes=str(token.get('scope') or '').split();expires_at=datetime.now(timezone.utc)+timedelta(seconds=int(token['expires_in'])) if token.get('expires_in') else None
        db.execute('INSERT INTO integration_connections(user_id,provider,access_token_ciphertext,refresh_token_ciphertext,token_type,scopes,expires_at) VALUES(%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(user_id,provider) DO UPDATE SET access_token_ciphertext=EXCLUDED.access_token_ciphertext,refresh_token_ciphertext=EXCLUDED.refresh_token_ciphertext,token_type=EXCLUDED.token_type,scopes=EXCLUDED.scopes,expires_at=EXCLUDED.expires_at,updated_at=now()',(row['user_id'],row['provider'],_seal(access),_seal(refresh) if refresh else None,token.get('token_type','Bearer'),scopes,expires_at));db.execute('UPDATE integration_oauth_states SET consumed_at=now() WHERE state_hash=%s',(state_hash,))
    return {'connected':True,'provider':row['provider']}

def connection_token(user_id:str,provider:str)->str|None:
    with _pool().connection() as db:row=db.execute('SELECT access_token_ciphertext FROM integration_connections WHERE user_id=%s AND provider=%s',(user_id,provider)).fetchone()
    return _open(row['access_token_ciphertext']) if row else None

def connection_providers(user_id:str)->list[str]:
    with _pool().connection() as db:rows=db.execute('SELECT provider FROM integration_connections WHERE user_id=%s',(user_id,)).fetchall()
    return [r['provider'] for r in rows]

def connection_summary(user_id:str)->list[dict[str,object]]:
    with _pool().connection() as db:rows=db.execute('SELECT provider,scopes,expires_at,updated_at FROM integration_connections WHERE user_id=%s ORDER BY provider',(user_id,)).fetchall()
    return [{'provider':r['provider'],'connected':True,'scopes':r['scopes'],'expires_at':r['expires_at'].isoformat() if r['expires_at'] else None,'updated_at':r['updated_at'].isoformat()} for r in rows]

def disconnect_connection(user_id:str,provider:str)->None:
    with _pool().connection() as db:db.execute('DELETE FROM integration_connections WHERE user_id=%s AND provider=%s',(user_id,provider))

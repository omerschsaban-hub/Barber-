from __future__ import annotations
import base64,hashlib,hmac,os,secrets,time
from email.message import EmailMessage
from typing import Any
import httpx
from fastapi import APIRouter,Header,HTTPException,Request
from pydantic import BaseModel,Field
from .postgres import execute,fetch_all,transaction
router=APIRouter(prefix='/auth',tags=['owned-auth'])
COOKIE_NAME='fabrient_session'; OTP_TTL_SECONDS=600; SESSION_TTL_SECONDS=2592000; MAX_OTP_ATTEMPTS=5
def _secret()->bytes:
 value=os.getenv('AUTH_SECRET')
 if not value or len(value)<32: raise RuntimeError('AUTH_SECRET must be configured with at least 32 bytes of entropy')
 return value.encode()
def _hash(value:str)->bytes:return hmac.new(_secret(),value.encode(),hashlib.sha256).digest()
def _client_ip(request:Request)->str:return request.client.host if request.client else 'unknown'
def _rate_limit(bucket:str,limit:int,window_seconds:int)->None:
 rows=fetch_all("INSERT INTO rate_limits(bucket,window_started_at,count) VALUES(%s,now(),1) ON CONFLICT(bucket) DO UPDATE SET count=CASE WHEN rate_limits.window_started_at<=now()-(%s*interval '1 second') THEN 1 ELSE rate_limits.count+1 END,window_started_at=CASE WHEN rate_limits.window_started_at<=now()-(%s*interval '1 second') THEN now() ELSE rate_limits.window_started_at END,updated_at=now() RETURNING count",(bucket,window_seconds,window_seconds))
 if rows and int(rows[0]['count'])>limit:raise HTTPException(429,'Too many requests. Please try again later.')
async def _gmail_access_token()->str:
 refresh,client_id,client_secret=os.getenv('GMAIL_REFRESH_TOKEN'),os.getenv('GMAIL_CLIENT_ID'),os.getenv('GMAIL_CLIENT_SECRET')
 if not refresh or not client_id or not client_secret:raise RuntimeError('Gmail OAuth credentials are not configured')
 async with httpx.AsyncClient(timeout=10) as client:r=await client.post('https://oauth2.googleapis.com/token',data={'client_id':client_id,'client_secret':client_secret,'refresh_token':refresh,'grant_type':'refresh_token'})
 if r.status_code!=200:raise RuntimeError('Gmail OAuth token refresh failed')
 token=r.json().get('access_token')
 if not token:raise RuntimeError('Gmail OAuth response did not contain an access token')
 return token
async def _send_otp_email(email:str,code:str)->None:
 token=await _gmail_access_token();msg=EmailMessage();msg['To']=email;msg['From']=os.getenv('GMAIL_SENDER','omerschsaban@gmail.com');msg['Subject']='Your Fabrient sign-in code';msg.set_content(f'Your Fabrient sign-in code is {code}. It expires in 10 minutes and can only be used once.');raw=base64.urlsafe_b64encode(msg.as_bytes()).decode().rstrip('=')
 async with httpx.AsyncClient(timeout=10) as client:r=await client.post('https://gmail.googleapis.com/gmail/v1/users/me/messages/send',headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},json={'raw':raw})
 if r.status_code>=300:raise RuntimeError('Gmail API rejected the OTP message')
class EmailRequest(BaseModel):email:str=Field(min_length=6,max_length=254)
class VerifyRequest(BaseModel):email:str=Field(min_length=6,max_length=254);code:str=Field(pattern=r'^\d{6}$')
class SessionResponse(BaseModel):user:dict[str,Any];session_token:str;expires_in:int
def _normalize_email(email:str)->str:
 n=email.strip().lower()
 if len(n)>254 or '@' not in n or not n.endswith('@gmail.com'):raise HTTPException(400,'Use a valid Gmail address.')
 return n
def _bearer(request:Request,authorization:str|None)->str|None:
 h=authorization or request.headers.get('authorization')
 return h[7:].strip() if h and h.lower().startswith('bearer ') else request.cookies.get(COOKIE_NAME)
def user_from_token(token:str|None)->dict[str,Any]|None:
 if not token:return None
 return fetch_one("select u.id::text as id,u.email,u.display_name,u.email_verified_at,u.role from sessions s join users u on u.id=s.user_id where s.token_hash=%s and s.revoked_at is null and s.expires_at>now()",(_hash(token),))
def _session(token:str|None)->dict[str,Any]|None:
 u=user_from_token(token);return {'user_id':u['id'],'email':u['email'],'display_name':u['display_name'],'role':u['role']} if u else None
@router.post('/request-otp')
async def request_otp(body:EmailRequest,request:Request):
 email=_normalize_email(body.email);_rate_limit('otp:ip:'+hashlib.sha256(_client_ip(request).encode()).hexdigest(),10,3600);_rate_limit('otp:email:'+hashlib.sha256(email.encode()).hexdigest(),5,3600);code=f'{secrets.randbelow(1000000):06d}';execute('update otp_challenges set consumed_at=now() where lower(email)=lower(%s) and consumed_at is null',(email,));execute("insert into otp_challenges(email,code_hash,attempts,expires_at) values(%s,%s,0,now()+(%s*interval '1 second'))",(email,_hash(code),OTP_TTL_SECONDS))
 try:await _send_otp_email(email,code)
 except Exception:execute('update otp_challenges set consumed_at=now() where lower(email)=lower(%s) and consumed_at is null',(email,));raise HTTPException(502,'Could not send the sign-in code.')
 return {'ok':True,'expires_in':OTP_TTL_SECONDS}
@router.post('/verify-otp',response_model=SessionResponse)
def verify_otp(body:VerifyRequest,request:Request):
 email=_normalize_email(body.email);_rate_limit('otp-verify:ip:'+hashlib.sha256(_client_ip(request).encode()).hexdigest(),20,3600)
 with transaction() as conn:
  ch=conn.execute("select id,code_hash,attempts,expires_at from otp_challenges where lower(email)=lower(%s) and consumed_at is null order by created_at desc limit 1 for update",(email,)).fetchone()
  if not ch or ch['expires_at'].timestamp()<=time.time() or int(ch['attempts'])>=MAX_OTP_ATTEMPTS:
   if ch:conn.execute('update otp_challenges set consumed_at=now() where id=%s',(ch['id'],))
   raise HTTPException(400,'That code is invalid or expired.')
  if not hmac.compare_digest(bytes(ch['code_hash']),_hash(body.code)):conn.execute('update otp_challenges set attempts=attempts+1 where id=%s',(ch['id'],));raise HTTPException(400,'That code is invalid or expired.')
  conn.execute('update otp_challenges set consumed_at=now() where id=%s',(ch['id'],));u=conn.execute("insert into users(email,email_verified_at) values(%s,now()) on conflict((lower(email))) do update set email_verified_at=coalesce(users.email_verified_at,now()),updated_at=now() returning id::text as id,email,display_name,email_verified_at,role",(email,)).fetchone();token=secrets.token_urlsafe(48);conn.execute("insert into sessions(user_id,token_hash,expires_at) values(%s,%s,now()+(%s*interval '1 second'))",(u['id'],_hash(token),SESSION_TTL_SECONDS));conn.execute("insert into audit_logs(user_id,action,resource_type,resource_id,metadata) values(%s,'auth.login','session',%s,%s::jsonb)",(u['id'],u['id'],'{"method":"gmail_otp"}'))
 return {'user':u,'session_token':token,'expires_in':SESSION_TTL_SECONDS}
@router.get('/me')
def me(request:Request,authorization:str|None=Header(default=None)):
 u=user_from_token(_bearer(request,authorization))
 if not u:raise HTTPException(401,'Unauthorized')
 return {'user':u}
@router.post('/logout')
def logout(request:Request,authorization:str|None=Header(default=None)):
 token=_bearer(request,authorization)
 if token:execute('update sessions set revoked_at=now() where token_hash=%s and revoked_at is null',(_hash(token),))
 return {'ok':True}

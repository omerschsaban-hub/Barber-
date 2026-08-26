from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any

import httpx
from fastapi import APIRouter, Cookie, Header, HTTPException, Response
from pydantic import BaseModel, EmailStr

try:
    from psycopg_pool import ConnectionPool
except ImportError:  # pragma: no cover
    ConnectionPool = None

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_TTL_SECONDS = 10 * 60
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60
OTP_RESEND_SECONDS = 60
MAX_OTP_ATTEMPTS = 8
COOKIE_NAME = "fabrient_session"


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _pool():
    if ConnectionPool is None:
        raise RuntimeError("psycopg_pool is not installed")
    dsn = _required("DATABASE_URL")
    return ConnectionPool(conninfo=dsn, min_size=1, max_size=int(os.getenv("DB_POOL_MAX", "8")), open=True)

_POOL = None


def db():
    global _POOL
    if _POOL is None:
        _POOL = _pool()
    return _POOL


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()


def _otp_hash(email: str, code: str) -> bytes:
    secret = _required("AUTH_SECRET").encode("utf-8")
    return hmac.new(secret, f"otp:{email}:{code}".encode("utf-8"), hashlib.sha256).digest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _token() -> str:
    return secrets.token_urlsafe(48)


class EmailRequest(BaseModel):
    email: EmailStr


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str


async def _gmail_send(to: str, code: str) -> None:
    client_id = _required("GOOGLE_CLIENT_ID")
    client_secret = _required("GOOGLE_CLIENT_SECRET")
    refresh_token = _required("GOOGLE_REFRESH_TOKEN")
    sender = os.getenv("AUTH_FROM_EMAIL", "omerschsaban@gmail.com")

    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        token_response.raise_for_status()
        access_token = token_response.json()["access_token"]

        message = EmailMessage()
        message["To"] = to
        message["From"] = sender
        message["Subject"] = "Your Fabrient sign-in code"
        message.set_content(
            f"Your Fabrient sign-in code is {code}.\n\n"
            "It expires in 10 minutes and can only be used once.\n"
            "If you did not request this code, you can ignore this email."
        )
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")
        send_response = await client.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": raw},
        )
        send_response.raise_for_status()


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=os.getenv("AUTH_COOKIE_SECURE", "true").lower() == "true",
        samesite="lax",
        path="/",
    )


def _session(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    with db().connection() as conn:
        row = conn.execute(
            """select u.id, u.email, u.display_name, u.email_verified_at, s.id as session_id
               from sessions s join users u on u.id=s.user_id
               where s.token_hash=%s and s.revoked_at is null and s.expires_at > now()""",
            (_digest(token),),
        ).fetchone()
        if not row:
            return None
        conn.execute("update sessions set last_seen_at=now() where id=%s", (row[4],))
        return {"user_id": str(row[0]), "email": row[1], "display_name": row[2], "email_verified": row[3] is not None}


@router.post("/request-code")
async def request_code(payload: EmailRequest):
    email = str(payload.email).strip().lower()
    # Generic response prevents account enumeration.
    with db().connection() as conn:
        recent = conn.execute(
            "select created_at from otp_challenges where email=%s order by created_at desc limit 1",
            (email,),
        ).fetchone()
        if recent and (_now() - recent[0]).total_seconds() < OTP_RESEND_SECONDS:
            return {"ok": True, "message": "If that address is eligible, a code has been sent."}
        code = f"{secrets.randbelow(1_000_000):06d}"
        conn.execute("update otp_challenges set consumed_at=now() where email=%s and consumed_at is null", (email,))
        conn.execute(
            "insert into otp_challenges(email, code_hash, expires_at) values (%s,%s,%s)",
            (email, _otp_hash(email, code), _now() + timedelta(seconds=OTP_TTL_SECONDS)),
        )
    try:
        await _gmail_send(email, code)
    except Exception:
        # Do not expose transport details. Remove the challenge so a failed send can be retried.
        with db().connection() as conn:
            conn.execute("delete from otp_challenges where email=%s and consumed_at is null", (email,))
        raise HTTPException(status_code=502, detail="Unable to send sign-in code")
    return {"ok": True, "message": "If that address is eligible, a code has been sent."}


@router.post("/verify-code")
def verify_code(payload: VerifyRequest, response: Response):
    email = str(payload.email).strip().lower()
    code = payload.code.strip()
    if not code.isdigit() or len(code) != 6:
        raise HTTPException(status_code=400, detail="Invalid code")
    with db().connection() as conn:
        row = conn.execute(
            """select id, code_hash, attempts from otp_challenges
               where email=%s and consumed_at is null and expires_at > now()
               order by created_at desc limit 1 for update""",
            (email,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="That code is invalid or expired")
        challenge_id, expected, attempts = row
        if attempts >= MAX_OTP_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Too many attempts; request a new code")
        if not hmac.compare_digest(expected, _otp_hash(email, code)):
            conn.execute("update otp_challenges set attempts=attempts+1 where id=%s", (challenge_id,))
            raise HTTPException(status_code=400, detail="That code is invalid or expired")
        conn.execute("update otp_challenges set consumed_at=now() where id=%s", (challenge_id,))
        user = conn.execute(
            "insert into users(email,email_verified_at) values (%s,now()) on conflict(email) do update set email_verified_at=coalesce(users.email_verified_at,now()), updated_at=now() returning id,email,display_name",
            (email,),
        ).fetchone()
        token = _token()
        conn.execute(
            "insert into sessions(user_id,token_hash,expires_at) values (%s,%s,%s)",
            (user[0], _digest(token), _now() + timedelta(seconds=SESSION_TTL_SECONDS)),
        )
    _set_cookie(response, token)
    return {"ok": True, "user": {"id": str(user[0]), "email": user[1], "display_name": user[2]}}


@router.post("/logout")
def logout(response: Response, session: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    if session:
        with db().connection() as conn:
            conn.execute("update sessions set revoked_at=now() where token_hash=%s and revoked_at is null", (_digest(session),))
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
def me(session: str | None = Cookie(default=None, alias=COOKIE_NAME), authorization: str | None = Header(default=None)):
    token = session
    if not token and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    identity = _session(token)
    if not identity:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user": identity}


def authenticate_bearer(authorization: str | None) -> dict[str, Any] | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return _session(authorization.split(" ", 1)[1].strip())

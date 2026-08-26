from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from fastapi import APIRouter, Cookie, Header, HTTPException, Request

from .owned_auth import _session, COOKIE_NAME
from .postgres import execute, fetch_all, fetch_one

router = APIRouter(prefix="/billing", tags=["billing"])
PRO_ENTITLEMENT = "create_an_app_called_fabrinat_pro"


def _verify_webhook(raw: bytes, authorization: str | None, signature: str | None) -> None:
    expected_auth = os.getenv("REVENUECAT_WEBHOOK_AUTH")
    secret = os.getenv("REVENUECAT_WEBHOOK_SIGNING_SECRET")
    if expected_auth and not authorization or (expected_auth and not hmac.compare_digest(authorization or "", expected_auth)):
        raise HTTPException(401, "Unauthorized")
    if secret:
        if not signature or not signature.startswith("t=") or ",v1=" not in signature:
            raise HTTPException(401, "Invalid webhook signature")
        ts, supplied = signature[2:].split(",v1=", 1)
        try: timestamp = int(ts)
        except ValueError: raise HTTPException(401, "Invalid webhook timestamp")
        if abs(time.time() - timestamp) > 300: raise HTTPException(401, "Stale webhook")
        digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(digest, supplied): raise HTTPException(401, "Invalid webhook signature")


@router.get("/access")
def access(session: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    identity = _session(session)
    if not identity: raise HTTPException(401, "Unauthorized")
    row = fetch_one("select entitlement_id,active,product_id,expires_at from billing_entitlements where user_id=%s and entitlement_id=%s", (identity["user_id"], PRO_ENTITLEMENT))
    pro = bool(row and row["active"] and (row["expires_at"] is None or row["expires_at"].timestamp() > time.time()))
    return {"authenticated": True, "pro": pro, "entitlement": PRO_ENTITLEMENT}


@router.post("/webhooks/revenuecat")
async def revenuecat_webhook(request: Request, authorization: str | None = Header(default=None), x_revenuecat_webhook_signature: str | None = Header(default=None)):
    raw = await request.body()
    _verify_webhook(raw, authorization, x_revenuecat_webhook_signature)
    body = json.loads(raw)
    event = body.get("event") or body
    event_id = str(event.get("id") or event.get("event_id") or "")
    if not event_id: raise HTTPException(400, "Missing event id")
    inserted = fetch_one("insert into billing_events(event_id,event_type,app_user_id,environment,payload) values(%s,%s,%s,%s,%s::jsonb) on conflict(event_id) do nothing returning event_id", (event_id,str(event.get("type","UNKNOWN")),str(event.get("app_user_id") or ""),str(event.get("environment") or ""),json.dumps(body)))
    if not inserted: return {"received": True, "duplicate": True}
    app_user_id = str(event.get("app_user_id") or "")
    user = fetch_one("select id from users where id::text=%s", (app_user_id,))
    if user:
        entitlements = event.get("entitlement_ids") or []
        event_type = str(event.get("type","")).upper()
        active = event_type not in {"EXPIRATION","CANCELLATION","BILLING_ISSUE"}
        for entitlement in entitlements:
            execute("""insert into billing_entitlements(user_id,entitlement_id,active,product_id,expires_at,source)
                       values(%s,%s,%s,%s,%s,'revenuecat')
                       on conflict(user_id,entitlement_id) do update set active=excluded.active,product_id=excluded.product_id,expires_at=excluded.expires_at,updated_at=now()""", (user["id"],str(entitlement),active,event.get("product_id"),None))
    execute("update billing_events set processed_at=now() where event_id=%s", (event_id,))
    return {"received": True, "processed": bool(user)}

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Header, HTTPException, Request

from .owned_auth import _bearer, user_from_token, COOKIE_NAME
from .postgres import transaction
from .plan_catalog import access_for_user

router = APIRouter(prefix="/billing", tags=["billing"])
PRO_ENTITLEMENT = "create_an_app_called_fabrinat_pro"


def _verify_webhook(raw: bytes, authorization: str | None, signature: str | None) -> None:
    expected_auth = os.getenv("REVENUECAT_WEBHOOK_AUTH")
    secret = os.getenv("REVENUECAT_WEBHOOK_SIGNING_SECRET")
    if expected_auth and (not authorization or not hmac.compare_digest(authorization, expected_auth)):
        raise HTTPException(401, "Unauthorized")
    if secret:
        if not signature or not signature.startswith("t=") or ",v1=" not in signature:
            raise HTTPException(401, "Invalid webhook signature")
        ts, supplied = signature[2:].split(",v1=", 1)
        try:
            timestamp = int(ts)
        except ValueError as exc:
            raise HTTPException(401, "Invalid webhook timestamp") from exc
        if abs(time.time() - timestamp) > 300:
            raise HTTPException(401, "Stale webhook")
        digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(digest, supplied):
            raise HTTPException(401, "Invalid webhook signature")


def _event_time(event: dict) -> datetime | None:
    value = event.get("event_timestamp_ms") or event.get("purchased_at_ms") or event.get("expiration_at_ms")
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


@router.get("/access")
def access(request: Request, authorization: str | None = Header(default=None), session: str | None = Cookie(default=None, alias=COOKIE_NAME)):
    identity = user_from_token(_bearer(request, authorization) or session)
    if not identity:
        raise HTTPException(401, "Unauthorized")
    resolved = access_for_user(identity["user_id"])
    return {
        "authenticated": True,
        "pro": resolved["plan"] != "free",
        "entitlement": PRO_ENTITLEMENT,
        **resolved,
    }


@router.post("/webhooks/revenuecat")
async def revenuecat_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
    x_revenuecat_webhook_signature: str | None = Header(default=None),
):
    raw = await request.body()
    _verify_webhook(raw, authorization, x_revenuecat_webhook_signature)
    try:
        body = json.loads(raw)
    except ValueError as exc:
        raise HTTPException(400, "Invalid JSON") from exc
    event = body.get("event") or body
    event_id = str(event.get("id") or event.get("event_id") or "")
    if not event_id:
        raise HTTPException(400, "Missing event id")

    app_user_id = str(event.get("app_user_id") or "")
    occurred_at = _event_time(event)
    event_type = str(event.get("type", "UNKNOWN")).upper()
    active = event_type not in {"EXPIRATION", "CANCELLATION", "BILLING_ISSUE"}
    expires_at = event.get("expiration_at_ms")
    expiry = None
    if expires_at:
        try:
            expiry = datetime.fromtimestamp(float(expires_at) / 1000, tz=timezone.utc)
        except (TypeError, ValueError, OverflowError):
            expiry = None
    entitlements = [str(x) for x in (event.get("entitlement_ids") or []) if x]

    with transaction() as conn:
        inserted = conn.execute(
            """insert into billing_events(event_id,event_type,app_user_id,environment,payload,occurred_at,sequence_number)
               values(%s,%s,%s,%s,%s::jsonb,%s,%s)
               on conflict(event_id) do nothing
               returning event_id""",
            (
                event_id,
                event_type,
                app_user_id,
                str(event.get("environment") or ""),
                json.dumps(body),
                occurred_at,
                int(event.get("event_timestamp_ms") or 0) if str(event.get("event_timestamp_ms") or "").isdigit() else None,
            ),
        ).fetchone()
        if not inserted:
            return {"received": True, "duplicate": True}

        customer = conn.execute(
            "select user_id from billing_customers where revenuecat_app_user_id=%s for update",
            (app_user_id,),
        ).fetchone()
        if not customer:
            return {"received": True, "processed": False, "reason": "unmapped_revenuecat_customer"}

        user_id = customer["user_id"]
        for entitlement in entitlements:
            current = conn.execute(
                "select updated_at from billing_entitlements where user_id=%s and entitlement_id=%s for update",
                (user_id, entitlement),
            ).fetchone()
            if current and occurred_at and current["updated_at"] > occurred_at:
                continue
            conn.execute(
                """insert into billing_entitlements(user_id,entitlement_id,active,product_id,expires_at,source)
                   values(%s,%s,%s,%s,%s,'revenuecat')
                   on conflict(user_id,entitlement_id) do update
                   set active=excluded.active,product_id=excluded.product_id,expires_at=excluded.expires_at,updated_at=now()""",
                (user_id, entitlement, active, event.get("product_id"), expiry),
            )
        conn.execute("update billing_events set processed_at=now() where event_id=%s", (event_id,))

    return {"received": True, "processed": True, "duplicate": False}

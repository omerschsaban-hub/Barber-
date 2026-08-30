from __future__ import annotations

import json
import os
from uuid import uuid4

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from .owned_auth import _bearer, user_from_token
from .postgres import transaction

router = APIRouter(prefix="/billing/paypal", tags=["paypal-billing"])

PLAN_CONFIG = {
    "hobbyist": ("PAYPAL_HOBBY_PLAN_ID", "hobby_monthly", "fabrinat_hobby"),
    "startup": ("PAYPAL_STARTUP_PLAN_ID", "startup_monthly", "fabrinat_startup"),
}


class CreateSubscriptionRequest(BaseModel):
    plan: str = Field(pattern=r"^(hobbyist|startup)$")


def _environment() -> str:
    return os.getenv("PAYPAL_ENVIRONMENT", "sandbox").strip().lower()


def _base_url() -> str:
    if _environment() == "production":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"


def _credentials() -> tuple[str, str]:
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_CLIENT_SECRET")
    if not client_id or not secret:
        raise HTTPException(503, "PayPal billing is not configured on the server.")
    return client_id, secret


async def _access_token(client: httpx.AsyncClient) -> str:
    client_id, secret = _credentials()
    response = await client.post(
        f"{_base_url()}/v1/oauth2/token",
        auth=(client_id, secret),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json", "Accept-Language": "en_US"},
    )
    if response.status_code >= 300:
        raise HTTPException(502, "PayPal authentication failed.")
    token = response.json().get("access_token")
    if not token:
        raise HTTPException(502, "PayPal did not return an access token.")
    return token


def _identity(request: Request, authorization: str | None) -> dict:
    identity = user_from_token(_bearer(request, authorization))
    if not identity:
        raise HTTPException(401, "Unauthorized")
    return identity


def _public_url() -> str:
    return os.getenv("FABRIENT_WEB_URL", "http://localhost:3000").rstrip("/")


@router.get("/config")
def paypal_config():
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    plans = {plan: os.getenv(env_name) for plan, (env_name, _, _) in PLAN_CONFIG.items()}
    configured = bool(client_id and all(plans.values()))
    return {
        "configured": configured,
        "environment": _environment(),
        "client_id": client_id if configured else None,
        "plans": plans if configured else {},
        "currency": "USD",
    }


@router.post("/create-subscription")
async def create_subscription(
    body: CreateSubscriptionRequest,
    request: Request,
    authorization: str | None = Header(default=None),
):
    identity = _identity(request, authorization)
    plan_env, product_id, entitlement_id = PLAN_CONFIG[body.plan]
    plan_id = os.getenv(plan_env)
    if not plan_id:
        raise HTTPException(503, f"PayPal {body.plan} plan is not configured.")

    with transaction() as conn:
        existing = conn.execute(
            """select paypal_subscription_id, status from paypal_subscriptions
               where user_id=%s and status in ('APPROVAL_PENDING','ACTIVE','SUSPENDED')
               order by created_at desc limit 1 for update""",
            (identity["id"],),
        ).fetchone()
        if existing:
            raise HTTPException(409, "An existing PayPal subscription must be resolved before starting another.")

    request_id = str(uuid4())
    payload = {
        "plan_id": plan_id,
        "custom_id": str(identity["id"]),
        "application_context": {
            "brand_name": "Fabrient",
            "locale": "en-US",
            "shipping_preference": "NO_SHIPPING",
            "user_action": "SUBSCRIBE_NOW",
            "return_url": f"{_public_url()}/billing?paypal=approved&plan={body.plan}",
            "cancel_url": f"{_public_url()}/billing?paypal=cancelled&plan={body.plan}",
        },
    }
    async with httpx.AsyncClient(timeout=15) as client:
        token = await _access_token(client)
        response = await client.post(
            f"{_base_url()}/v1/billing/subscriptions",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json", "PayPal-Request-Id": request_id},
            json=payload,
        )
    if response.status_code >= 300:
        raise HTTPException(502, "PayPal could not create the subscription.")
    created = response.json()
    subscription_id = created.get("id")
    approve = next((link.get("href") for link in created.get("links", []) if link.get("rel") == "approve"), None)
    if not subscription_id or not approve:
        raise HTTPException(502, "PayPal returned an incomplete subscription response.")

    with transaction() as conn:
        conn.execute(
            """insert into paypal_subscriptions
               (paypal_subscription_id,user_id,plan,product_id,entitlement_id,status,environment,request_id,payload)
               values(%s,%s,%s,%s,%s,'APPROVAL_PENDING',%s,%s,%s::jsonb)
               on conflict(paypal_subscription_id) do nothing""",
            (subscription_id, identity["id"], body.plan, product_id, entitlement_id, _environment(), request_id, json.dumps(created)),
        )
    return {"subscription_id": subscription_id, "approval_url": approve, "status": "APPROVAL_PENDING"}


async def _verify_paypal_webhook(headers: dict[str, str], event: dict) -> None:
    webhook_id = os.getenv("PAYPAL_WEBHOOK_ID")
    if not webhook_id:
        raise HTTPException(503, "PayPal webhook verification is not configured.")
    async with httpx.AsyncClient(timeout=15) as client:
        token = await _access_token(client)
        response = await client.post(
            f"{_base_url()}/v1/notifications/verify-webhook-signature",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "auth_algo": headers.get("paypal-auth-algo"),
                "cert_url": headers.get("paypal-cert-url"),
                "transmission_id": headers.get("paypal-transmission-id"),
                "transmission_sig": headers.get("paypal-transmission-sig"),
                "transmission_time": headers.get("paypal-transmission-time"),
                "webhook_id": webhook_id,
                "webhook_event": event,
            },
        )
    if response.status_code >= 300 or response.json().get("verification_status") != "SUCCESS":
        raise HTTPException(401, "Invalid PayPal webhook signature.")


@router.post("/webhook")
async def paypal_webhook(request: Request):
    raw = await request.body()
    try:
        event = json.loads(raw)
    except ValueError as exc:
        raise HTTPException(400, "Invalid JSON") from exc
    headers = {key.lower(): value for key, value in request.headers.items()}
    await _verify_paypal_webhook(headers, event)
    event_id = str(event.get("id") or "")
    if not event_id:
        raise HTTPException(400, "Missing PayPal event ID")
    event_type = str(event.get("event_type") or "UNKNOWN")
    resource = event.get("resource") or {}
    subscription_id = str(resource.get("id") or resource.get("billing_agreement_id") or resource.get("subscription_id") or "")
    active = event_type in {"BILLING.SUBSCRIPTION.ACTIVATED", "PAYMENT.SALE.COMPLETED"}
    inactive = event_type in {"BILLING.SUBSCRIPTION.CANCELLED", "BILLING.SUBSCRIPTION.EXPIRED", "BILLING.SUBSCRIPTION.SUSPENDED", "BILLING.SUBSCRIPTION.PAYMENT.FAILED", "PAYMENT.SALE.REFUNDED", "PAYMENT.SALE.REVERSED"}
    with transaction() as conn:
        inserted = conn.execute(
            """insert into billing_events(event_id,event_type,app_user_id,environment,payload,occurred_at)
               values(%s,%s,%s,%s,%s::jsonb,coalesce(%s,now())) on conflict(event_id) do nothing returning event_id""",
            (event_id, event_type, str(resource.get("custom_id") or ""), _environment(), json.dumps(event), event.get("create_time")),
        ).fetchone()
        if not inserted:
            return {"received": True, "duplicate": True}
        if not subscription_id or not (active or inactive):
            conn.execute("update billing_events set processed_at=now() where event_id=%s", (event_id,))
            return {"received": True, "processed": False, "reason": "unhandled_event"}
        subscription = conn.execute("select user_id,entitlement_id,product_id from paypal_subscriptions where paypal_subscription_id=%s for update", (subscription_id,)).fetchone()
        if not subscription:
            return {"received": True, "processed": False, "reason": "unmapped_subscription"}
        status = "ACTIVE" if active else "INACTIVE"
        conn.execute("update paypal_subscriptions set status=%s,updated_at=now(),last_event_id=%s where paypal_subscription_id=%s", (status, event_id, subscription_id))
        conn.execute(
            """insert into billing_entitlements(user_id,entitlement_id,active,product_id,source)
               values(%s,%s,%s,%s,'paypal') on conflict(user_id,entitlement_id) do update
               set active=excluded.active,product_id=excluded.product_id,updated_at=now(),source='paypal'""",
            (subscription["user_id"], subscription["entitlement_id"], active, subscription["product_id"]),
        )
        conn.execute("update billing_events set processed_at=now() where event_id=%s", (event_id,))
    return {"received": True, "processed": True, "duplicate": False}


@router.get("/status")
def paypal_status(request: Request, authorization: str | None = Header(default=None)):
    identity = _identity(request, authorization)
    with transaction() as conn:
        row = conn.execute(
            """select paypal_subscription_id,plan,status,environment,created_at,updated_at
               from paypal_subscriptions where user_id=%s order by updated_at desc limit 1""",
            (identity["id"],),
        ).fetchone()
    return {"subscription": row}

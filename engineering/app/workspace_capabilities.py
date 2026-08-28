from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field, HttpUrl

from .owned_auth import _bearer, user_from_token
from .postgres import fetch_all, fetch_one, transaction

router = APIRouter(prefix="/v1", tags=["workspace-capabilities"])


def identity(request: Request, authorization: str | None) -> dict[str, Any]:
    user = user_from_token(_bearer(request, authorization))
    api_key = request.headers.get("x-api-key")
    if not user and api_key:
        digest = hmac.new(os.getenv("AUTH_SECRET", "development-only").encode(), api_key.encode(), hashlib.sha256).digest()
        key_user = fetch_one("select u.id::text as id,u.email,u.display_name,u.role from api_keys k join users u on u.id=k.user_id where k.key_hash=%s and k.revoked_at is null and (k.expires_at is null or k.expires_at>now())", (digest,))
        user = key_user
    if not user:
        raise HTTPException(401, "Authentication required")
    return user


def organization(user_id: str) -> dict[str, Any]:
    row = fetch_one(
        """select o.id::text as id,o.name,om.role from organizations o
           join organization_members om on om.organization_id=o.id
           where om.user_id=%s order by o.created_at limit 1""", (user_id,))
    if row:
        return row
    with transaction() as conn:
        org = conn.execute("insert into organizations(name) values(%s) returning id::text as id,name", ("Personal workspace",)).fetchone()
        conn.execute("insert into organization_members(organization_id,user_id,role) values(%s,%s,'owner')", (org["id"], user_id))
    return {**org, "role": "owner"}


def require_admin(org: dict[str, Any]) -> None:
    if org["role"] not in {"admin", "owner"}:
        raise HTTPException(403, "Workspace admin permission required")


class Invitation(BaseModel):
    email: str = Field(min_length=6, max_length=254)
    role: str = Field(default="member", pattern="^(member|admin|owner)$")


class ApprovalRequest(BaseModel):
    project_id: str
    action: str = Field(min_length=2, max_length=120)
    note: str | None = Field(default=None, max_length=2000)


class ApprovalReview(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    note: str | None = Field(default=None, max_length=2000)


class WebhookRequest(BaseModel):
    url: HttpUrl
    events: list[str] = Field(default_factory=lambda: ["*"])


class PolicyRequest(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class ApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    expires_at: str | None = None


@router.get("/workspace")
def workspace(request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization)
    org = organization(user["id"])
    members = fetch_all("""select u.id::text as id,u.email,u.display_name,om.role,om.created_at
                          from organization_members om join users u on u.id=om.user_id
                          where om.organization_id=%s order by om.created_at limit 200""", (org["id"],))
    projects = fetch_all("""select p.id::text as id,p.name,p.created_at,pm.role
                           from projects p join project_members pm on pm.project_id=p.id
                           where pm.user_id=%s order by p.created_at desc limit 100""", (user["id"],))
    return {"organization": org, "members": members, "projects": projects}


@router.post("/workspace/invitations")
def invite(body: Invitation, request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization); org = organization(user["id"]); require_admin(org)
    with transaction() as conn:
        row = conn.execute("""insert into workspace_invitations(organization_id,email,role,invited_by)
                              values(%s,lower(%s),%s,%s) returning id::text as id,email,role,expires_at""", (org["id"], body.email, body.role, user["id"])).fetchone()
        conn.execute("insert into audit_logs(user_id,organization_id,action,resource_type,resource_id,metadata) values(%s,%s,'workspace.invite','invitation',%s,%s::jsonb)", (user["id"], org["id"], row["id"], '{"delivery":"pending"}'))
    return {"invitation": row, "delivery": "pending", "next_step": "send the invitation through the configured email provider"}


@router.post("/workspace/approvals")
def create_approval(body: ApprovalRequest, request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization)
    project = fetch_one("select id::text as id,organization_id::text as organization_id from projects where id=%s", (body.project_id,))
    if not project: raise HTTPException(404, "Project not found")
    member = fetch_one("select role from project_members where project_id=%s and user_id=%s", (body.project_id, user["id"]))
    if not member: raise HTTPException(403, "Project membership required")
    with transaction() as conn:
        row = conn.execute("""insert into project_approvals(project_id,requested_by,action,note)
                              values(%s,%s,%s,%s) returning id::text as id,project_id::text as project_id,action,status,note,created_at""", (body.project_id, user["id"], body.action, body.note)).fetchone()
        conn.execute("insert into audit_logs(user_id,organization_id,action,resource_type,resource_id,metadata) values(%s,%s,'approval.requested','project_approval',%s,%s::jsonb)", (user["id"], project["organization_id"], row["id"], '{"status":"pending"}'))
    return row


@router.get("/workspace/approvals")
def approvals(request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization)
    return {"approvals": fetch_all("""select a.id::text as id,a.project_id::text as project_id,a.action,a.status,a.note,a.created_at,a.reviewed_at
                                      from project_approvals a join project_members pm on pm.project_id=a.project_id
                                      where pm.user_id=%s order by a.created_at desc limit 100""", (user["id"],))}


@router.patch("/workspace/approvals/{approval_id}")
def review_approval(approval_id: str, body: ApprovalReview, request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization)
    row = fetch_one("""select a.id::text as id,a.project_id::text as project_id,p.organization_id::text as organization_id
                      from project_approvals a join projects p on p.id=a.project_id join project_members pm on pm.project_id=p.id
                      where a.id=%s and pm.user_id=%s and pm.role in ('admin','owner')""", (approval_id, user["id"]))
    if not row: raise HTTPException(404, "Approval not found or reviewer permission missing")
    with transaction() as conn:
        updated = conn.execute("""update project_approvals set status=%s,note=%s,reviewed_by=%s,reviewed_at=now()
                                  where id=%s and status='pending' returning id::text as id,status,note,reviewed_at""", (body.status, body.note, user["id"], approval_id)).fetchone()
        if not updated: raise HTTPException(409, "Approval is no longer pending")
        conn.execute("insert into audit_logs(user_id,organization_id,action,resource_type,resource_id,metadata) values(%s,%s,%s,'project_approval',%s,%s::jsonb)", (user["id"], row["organization_id"], f"approval.{body.status}", approval_id, '{"reviewed":true}'))
    return updated


@router.get("/notifications")
def notifications(request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization)
    return {"notifications": fetch_all("select id::text as id,kind,title,body,read_at,created_at from notifications where user_id=%s order by created_at desc limit 100", (user["id"],))}


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str, request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization)
    row = fetch_one("update notifications set read_at=coalesce(read_at,now()) where id=%s and user_id=%s returning id::text as id,read_at", (notification_id, user["id"]))
    if not row: raise HTTPException(404, "Notification not found")
    return row


@router.get("/organization/policy")
def get_policy(request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization); org = organization(user["id"])
    row = fetch_one("select settings,updated_at from organization_policies where organization_id=%s", (org["id"],))
    return {"organization_id": org["id"], "settings": row["settings"] if row else {}, "updated_at": row["updated_at"] if row else None}


@router.put("/organization/policy")
def set_policy(body: PolicyRequest, request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization); org = organization(user["id"]); require_admin(org)
    with transaction() as conn:
        row = conn.execute("""insert into organization_policies(organization_id,settings,updated_by)
                              values(%s,%s::jsonb,%s) on conflict(organization_id) do update set settings=excluded.settings,updated_by=excluded.updated_by,updated_at=now()
                              returning settings,updated_at""", (org["id"], __import__("json").dumps(body.settings), user["id"])).fetchone()
        conn.execute("insert into audit_logs(user_id,organization_id,action,resource_type,metadata) values(%s,%s,'organization.policy.updated','organization',%s::jsonb)", (user["id"], org["id"], '{"updated":true}'))
    return row


@router.post("/developer/api-keys")
def create_api_key(body: ApiKeyRequest, request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization)
    raw = "fab_" + secrets.token_urlsafe(32); digest = hmac.new(os.getenv("AUTH_SECRET", "development-only").encode(), raw.encode(), hashlib.sha256).digest()
    with transaction() as conn:
        row = conn.execute("insert into api_keys(user_id,name,key_prefix,key_hash,expires_at) values(%s,%s,%s,%s,%s) returning id::text as id,name,key_prefix,expires_at,created_at", (user["id"], body.name, raw[:12], digest, body.expires_at)).fetchone()
    return {"key": raw, "metadata": row, "warning": "The secret is shown once and cannot be recovered."}


@router.get("/developer/api-keys")
def list_api_keys(request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization)
    return {"keys": fetch_all("select id::text as id,name,key_prefix,expires_at,revoked_at,created_at from api_keys where user_id=%s order by created_at desc limit 100", (user["id"],))}


@router.delete("/developer/api-keys/{key_id}")
def revoke_api_key(key_id: str, request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization)
    row = fetch_one("update api_keys set revoked_at=coalesce(revoked_at,now()) where id=%s and user_id=%s returning id::text as id,revoked_at", (key_id, user["id"]))
    if not row: raise HTTPException(404, "API key not found")
    return row


@router.post("/developer/webhooks")
def create_webhook(body: WebhookRequest, request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization); org = organization(user["id"]); require_admin(org)
    secret = "whsec_" + secrets.token_urlsafe(30)
    digest = hmac.new(os.getenv("AUTH_SECRET", "development-only").encode(), secret.encode(), hashlib.sha256).digest()
    with transaction() as conn:
        row = conn.execute("insert into webhook_subscriptions(organization_id,url,secret_hash,events,created_by) values(%s,%s,%s,%s,%s) returning id::text as id,url,events,active,created_at", (org["id"], str(body.url), digest, body.events, user["id"])).fetchone()
    return {"webhook": row, "secret": secret, "warning": "The signing secret is shown once and cannot be recovered."}


@router.get("/developer/webhooks")
def list_webhooks(request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization); org = organization(user["id"]); require_admin(org)
    return {"webhooks": fetch_all("select id::text as id,url,events,active,created_at from webhook_subscriptions where organization_id=%s order by created_at desc limit 100", (org["id"],))}


@router.delete("/developer/webhooks/{webhook_id}")
def delete_webhook(webhook_id: str, request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization); org = organization(user["id"]); require_admin(org)
    row = fetch_one("delete from webhook_subscriptions where id=%s and organization_id=%s returning id::text as id", (webhook_id, org["id"]))
    if not row: raise HTTPException(404, "Webhook not found")
    return {"deleted": True, **row}


@router.get("/audit")
def audit(request: Request, authorization: str | None = Header(default=None)):
    user = identity(request, authorization); org = organization(user["id"])
    if org["role"] not in {"admin", "owner"}: raise HTTPException(403, "Audit permission required")
    return {"events": fetch_all("select id::text as id,action,resource_type,resource_id,metadata,created_at from audit_logs where organization_id=%s order by created_at desc limit 200", (org["id"],))}

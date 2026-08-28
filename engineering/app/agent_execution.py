from __future__ import annotations

import uuid
from typing import Any, Literal

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from .owned_auth import user_from_token
from .postgres import fetch_all, fetch_one, transaction

router = APIRouter(prefix="/v1/agent", tags=["agent-execution"])

ACTIONS = {
    "inspect_job": {"kind": "read", "requires_approval": False},
    "analyze_design": {"kind": "analyze", "requires_approval": False},
    "propose_change": {"kind": "modify", "requires_approval": True},
    "verify_design": {"kind": "verify", "requires_approval": False},
    "submit_physical_evidence": {"kind": "evidence", "requires_approval": False},
    "prepare_release": {"kind": "release", "requires_approval": True},
}

DEFAULT_COMPLETION = [
    "requested outcome produced",
    "required verification gates passed",
    "required evidence recorded",
    "manufacturing artifacts available when applicable",
]


class JobCreate(BaseModel):
    objective: str = Field(min_length=3, max_length=4000)
    project_id: str | None = None
    constraints: dict[str, Any] = Field(default_factory=dict)
    inputs: dict[str, Any] = Field(default_factory=dict)
    evidence_requirements: list[str] = Field(default_factory=list)
    completion_criteria: list[str] = Field(default_factory=lambda: list(DEFAULT_COMPLETION))


class ActionRequest(BaseModel):
    action: str = Field(min_length=2, max_length=100)
    inputs: dict[str, Any] = Field(default_factory=dict)
    actor_type: Literal["agent", "human"] = "agent"
    approved: bool = False


class ApprovalRequest(BaseModel):
    action: str = Field(min_length=2, max_length=100)
    approved: bool = True


def _user(request: Request, authorization: str | None) -> dict[str, Any]:
    header = authorization or request.headers.get("authorization")
    token = header[7:].strip() if header and header.lower().startswith("bearer ") else request.cookies.get("fabrient_session")
    user = user_from_token(token)
    if not user:
        raise HTTPException(401, "Unauthorized")
    return user


def _job(job_id: str, user_id: str) -> dict[str, Any]:
    row = fetch_one("select * from agent_jobs where id=%s and user_id=%s", (job_id, user_id))
    if not row:
        raise HTTPException(404, "Engineering job not found")
    return row


def _next(job: dict[str, Any]) -> dict[str, Any]:
    action = str(job["next_action"])
    policy = ACTIONS.get(action, {"kind": "unknown", "requires_approval": False})
    return {
        "action": action,
        "kind": policy["kind"],
        "requires_approval": policy["requires_approval"],
        "reason": job.get("blocker", {}).get("reason") if isinstance(job.get("blocker"), dict) else None,
        "allowed": action in ACTIONS,
    }


def _safe_job(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "project_id": str(row["project_id"]) if row.get("project_id") else None,
        "objective": row["objective"],
        "constraints": row["constraints"] or {},
        "inputs": row["inputs"] or {},
        "evidence_requirements": row["evidence_requirements"] or [],
        "allowed_actions": row["allowed_actions"] or [],
        "approvals": row["approvals"] or {},
        "state": row["state"],
        "status": row["status"],
        "next_action": row["next_action"],
        "next": _next(row),
        "blocker": row.get("blocker"),
        "completion_criteria": row["completion_criteria"] or [],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/capabilities")
def capabilities():
    return {
        "name": "Fabrient Agent Execution",
        "model": "job_state_machine",
        "principles": ["structured_state", "evidence_first", "bounded_actions", "human_gates", "resumable"],
        "outcome_workflows": ["engineer_job", "inspect_job", "verify_design", "prepare_release", "calibrate_from_build"],
        "actions": {name: {"kind": meta["kind"], "requires_approval": meta["requires_approval"]} for name, meta in ACTIONS.items()},
    }


@router.post("/jobs")
def create_job(body: JobCreate, request: Request, authorization: str | None = Header(default=None)):
    user = _user(request, authorization)
    job_id = str(uuid.uuid4())
    allowed = list(ACTIONS.keys())
    with transaction() as conn:
        row = conn.execute(
            """insert into agent_jobs
               (id,user_id,project_id,objective,constraints,inputs,evidence_requirements,allowed_actions,completion_criteria)
               values(%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb,%s::jsonb)
               returning *""",
            (job_id, user["id"], body.project_id, body.objective, body.constraints, body.inputs,
             body.evidence_requirements, allowed, body.completion_criteria),
        ).fetchone()
        conn.execute(
            """insert into agent_action_ledger(job_id,user_id,actor_type,action,status,inputs,outputs,evidence,decision_basis)
               values(%s,%s,'system','job.created','completed',%s::jsonb,%s::jsonb,'[]'::jsonb,%s)""",
            (job_id, user["id"], body.model_dump_json(), '{"state":"defined","next_action":"inspect_job"}',
             "Job contract accepted; no engineering claim made."),
        )
    return _safe_job(row)


@router.get("/jobs/{job_id}")
def get_job(job_id: str, request: Request, authorization: str | None = Header(default=None)):
    return _safe_job(_job(job_id, _user(request, authorization)["id"]))


@router.get("/jobs/{job_id}/state")
def get_job_state(job_id: str, request: Request, authorization: str | None = Header(default=None)):
    row = _job(job_id, _user(request, authorization)["id"])
    ledger = fetch_all("select action,status,actor_type,outputs,evidence,decision_basis,request_id,created_at from agent_action_ledger where job_id=%s order by created_at desc limit 20", (job_id,))
    artifacts = fetch_all("select id,artifact_type,name,uri,sha256,metadata,created_at from agent_artifacts where job_id=%s order by created_at desc", (job_id,))
    result = _safe_job(row)
    result["ledger_tail"] = ledger
    result["artifacts"] = artifacts
    result["resume"] = {"can_resume": row["status"] != "released", "next": _next(row)}
    return result


@router.get("/jobs/{job_id}/next-action")
def next_action(job_id: str, request: Request, authorization: str | None = Header(default=None)):
    row = _job(job_id, _user(request, authorization)["id"])
    return {"job_id": job_id, "state": row["state"], "status": row["status"], **_next(row)}


@router.get("/jobs/{job_id}/ledger")
def ledger(job_id: str, request: Request, authorization: str | None = Header(default=None)):
    user = _user(request, authorization)
    _job(job_id, user["id"])
    return {"job_id": job_id, "records": fetch_all("select * from agent_action_ledger where job_id=%s order by created_at asc", (job_id,))}


@router.get("/jobs/{job_id}/artifacts")
def artifacts(job_id: str, request: Request, authorization: str | None = Header(default=None)):
    user = _user(request, authorization)
    _job(job_id, user["id"])
    return {"job_id": job_id, "artifacts": fetch_all("select * from agent_artifacts where job_id=%s order by created_at asc", (job_id,))}


@router.post("/jobs/{job_id}/approvals")
def approval(job_id: str, body: ApprovalRequest, request: Request, authorization: str | None = Header(default=None)):
    user = _user(request, authorization)
    row = _job(job_id, user["id"])
    policy = ACTIONS.get(body.action)
    if not policy or not policy["requires_approval"]:
        raise HTTPException(400, "That action does not require a human approval gate")
    approvals = dict(row.get("approvals") or {})
    approvals[body.action] = {"approved": body.approved, "by": str(user["id"]) }
    with transaction() as conn:
        conn.execute("update agent_jobs set approvals=%s::jsonb where id=%s and user_id=%s", (approvals, job_id, user["id"]))
        conn.execute("insert into agent_action_ledger(job_id,user_id,actor_type,action,status,inputs,outputs,evidence,decision_basis) values(%s,%s,'human','approval.'||%s,'completed',%s::jsonb,%s::jsonb,'[]'::jsonb,%s)",
                     (job_id, user["id"], body.action, body.model_dump_json(), '{"approved":true}', "Explicit human approval recorded."))
    return {"job_id": job_id, "action": body.action, "approved": body.approved}


@router.post("/jobs/{job_id}/actions")
def perform_action(job_id: str, body: ActionRequest, request: Request, authorization: str | None = Header(default=None)):
    user = _user(request, authorization)
    row = _job(job_id, user["id"])
    policy = ACTIONS.get(body.action)
    if not policy:
        raise HTTPException(400, "Unknown action")
    if body.action != row["next_action"]:
        raise HTTPException(409, f"Action is not valid for the current job state; next action is {row['next_action']}")
    if policy["requires_approval"] and not (row.get("approvals") or {}).get(body.action, {}).get("approved"):
        with transaction() as conn:
            conn.execute("insert into agent_action_ledger(job_id,user_id,actor_type,action,status,inputs,outputs,evidence,decision_basis) values(%s,%s,%s,%s,'blocked',%s::jsonb,%s::jsonb,'[]'::jsonb,%s)",
                         (job_id, user["id"], body.actor_type, body.action, body.model_dump_json(), '{"requires_approval":true}', "Consequential action requires explicit human approval."))
        return {"job_id": job_id, "status": "blocked", "engineering_claims": False, "reason": "human_approval_required", "next": _next(row)}

    transitions = {
        "inspect_job": ("analyzing", "analyze_design"),
        "analyze_design": ("ready", "propose_change"),
        "propose_change": ("verifying", "verify_design"),
        "verify_design": ("ready", "prepare_release"),
        "submit_physical_evidence": ("verifying", "verify_design"),
        "prepare_release": ("ready", "prepare_release"),
    }
    state, next_name = transitions[body.action]
    if body.action == "prepare_release":
        next_name = "prepare_release"
    with transaction() as conn:
        output = {"accepted": True, "state_transition": {"state": state, "next_action": next_name}}
        conn.execute("update agent_jobs set state=%s,status='active',next_action=%s,blocker=null where id=%s and user_id=%s", (state, next_name, job_id, user["id"]))
        conn.execute("insert into agent_action_ledger(job_id,user_id,actor_type,action,status,inputs,outputs,evidence,decision_basis,request_id) values(%s,%s,%s,%s,'completed',%s::jsonb,%s::jsonb,'[]'::jsonb,%s,%s)",
                     (job_id, user["id"], body.actor_type, body.action, body.model_dump_json(), output, "Action accepted at the bounded job-state boundary; engineering result must come from the underlying deterministic tool.", request.headers.get("x-request-id")))
    return {"job_id": job_id, "status": "completed", "engineering_claims": False, "output": output, "next": {"action": next_name, "kind": ACTIONS[next_name]["kind"], "requires_approval": ACTIONS[next_name]["requires_approval"]}}

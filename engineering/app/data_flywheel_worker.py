from __future__ import annotations

import hashlib, json
from datetime import datetime, timezone

from fastapi import APIRouter, Header, HTTPException
import requests

from .data_flywheel import SOURCES, SUPABASE_URL, headers, post, INGEST_SECRET
from .data_flywheel_agents import run_bounded_flywheel

router = APIRouter(prefix="/data-flywheel", tags=["data-flywheel-worker"])


def _query(path: str, params: dict[str, str]) -> list[dict]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=headers(), params=params, timeout=20)
    if r.status_code >= 300:
        raise HTTPException(502, "Supabase read failed")
    return r.json()


@router.post("/worker")
def worker(x_fabrient_ingest_secret: str | None = Header(default=None)):
    if INGEST_SECRET and x_fabrient_ingest_secret != INGEST_SECRET:
        raise HTTPException(401, "Invalid ingestion secret")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    run_key = hashlib.sha256(f"fabrient-data-flywheel:{now.strftime('%Y-%m-%dT%H:%MZ')[:-1]}".encode()).hexdigest()
    existing = _query("data_observations", {"content_hash": f"eq.{run_key}", "select": "id", "limit": "1"})
    if existing:
        return {"ok": True, "idempotent": True, "run_id": run_key, "status": "already_completed"}

    # Record the run marker first. If the same schedule fires twice, the second
    # invocation becomes a no-op instead of duplicating observations/candidates.
    post("data_observations", {
        "source_key": "closed_loop",
        "event_type": "flywheel_run",
        "observed_at": now.isoformat(),
        "raw_payload": {"run_id": run_key, "trigger": "scheduled_or_manual"},
        "normalized_payload": {"run_id": run_key},
        "provenance": {"component": "data_flywheel_worker", "version": "1"},
        "consent_state": "not_applicable",
        "validation_state": "validated",
        "quality_score": 1.0,
        "content_hash": run_key,
    })

    # The existing 100-source registry remains authoritative; this worker never
    # seeds or creates a second catalog.
    enabled = _query("data_sources", {"enabled": "eq.true", "select": "key,name,enabled,collection_mode,consent_required,priority", "order": "priority.desc"})
    agent_results = run_bounded_flywheel(run_key)
    return {
        "ok": True,
        "idempotent": False,
        "run_id": run_key,
        "registered_sources": len(SOURCES),
        "enabled_sources": len(enabled),
        "agents": agent_results,
    }

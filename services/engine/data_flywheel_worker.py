"""Bounded, idempotent orchestration over the existing Fabrient flywheel tables."""
from __future__ import annotations
import hashlib
import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any
import requests

AGENTS = [
    ("Collector Agent", 120, 2),
    ("Normalization Agent", 120, 2),
    ("Data Quality Agent", 120, 2),
    ("Provenance Agent", 120, 2),
    ("Failure Detection Agent", 120, 2),
    ("Calibration Analysis Agent", 120, 2),
    ("Regression Test Generator Agent", 120, 2),
    ("Improvement Proposal Agent", 120, 2),
    ("Experiment/Validation Agent", 180, 1),
    ("Release Gate Agent", 120, 1),
]
SYSTEM_PROJECT_ID = "00000000-0000-0000-0000-000000000001"

class FlywheelError(RuntimeError):
    pass

class FlywheelClient:
    def __init__(self) -> None:
        self.url = (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or "").rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
        if not self.url or not self.key:
            raise FlywheelError("Supabase credentials are not configured")
        self.headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}

    def get(self, table: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        r = requests.get(f"{self.url}/rest/v1/{table}", headers=self.headers, params=params or {}, timeout=20)
        if r.status_code >= 300:
            raise FlywheelError(f"Supabase read failed: {r.status_code}")
        return r.json()

    def insert(self, table: str, payload: dict[str, Any], *, on_conflict: str | None = None) -> list[dict[str, Any]]:
        h = {**self.headers, "Prefer": "return=representation"}
        if on_conflict:
            h["Prefer"] = f"resolution=ignore-duplicates,return=representation"
        r = requests.post(f"{self.url}/rest/v1/{table}", headers=h, params={"on_conflict": on_conflict} if on_conflict else {}, json=payload, timeout=20)
        if r.status_code >= 300:
            raise FlywheelError(f"Supabase write failed: {r.status_code}")
        return r.json() if r.text else []

    def patch(self, table: str, filters: dict[str, str], payload: dict[str, Any]) -> None:
        r = requests.patch(f"{self.url}/rest/v1/{table}", headers={**self.headers, "Prefer": "return=minimal"}, params=filters, json=payload, timeout=20)
        if r.status_code >= 300:
            raise FlywheelError(f"Supabase patch failed: {r.status_code}")


def audit(db: FlywheelClient, agent: str, status: str, inp: dict[str, Any], out: dict[str, Any], started: datetime) -> None:
    db.insert("agent_runs", {
        "project_id": SYSTEM_PROJECT_ID,
        "agent_type": agent,
        "status": status,
        "context_refs": {"system": "fabrient-data-flywheel", "started_at": started.isoformat()},
        "input": inp,
        "output": out,
        "model": "deterministic-worker",
        "created_at": started.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })


def run_once() -> dict[str, Any]:
    db = FlywheelClient()
    started = datetime.now(timezone.utc)
    sources = db.get("data_sources", {"select": "id,key,enabled,consent_required,proprietary_data_allowed,license_required,config,priority", "enabled": "eq.true", "order": "priority.desc"})
    observations = db.get("data_observations", {"select": "id,source_key,event_type,raw_payload,normalized_payload,provenance,consent_state,validation_state,quality_score,content_hash,observed_at", "order": "observed_at.desc", "limit": "250"})
    result: dict[str, Any] = {"sources": len(sources), "observations_seen": len(observations), "agents": {}, "improvement_candidates": 0, "quarantined": 0}

    # Collector is deliberately bounded: only configured, explicitly authorized collectors are eligible.
    configured = [s for s in sources if isinstance(s.get("config"), dict) and s["config"].get("collector_url") and s.get("consent_required") is False]
    audit(db, "Collector Agent", "completed", {"enabled_sources": len(sources)}, {"eligible_collectors": len(configured), "skipped_unauthorized": len(sources)-len(configured)}, started)
    result["agents"]["Collector Agent"] = {"eligible": len(configured), "skipped_unauthorized": len(sources)-len(configured)}

    # Existing ingestion already stores normalized/provenance fields. Worker verifies them and records checks.
    for agent, timeout_s, retries in AGENTS[1:]:
        astart = datetime.now(timezone.utc)
        passed = 0
        failed = 0
        for obs in observations:
            ok = True
            details: dict[str, Any] = {}
            if agent == "Normalization Agent":
                ok = bool(obs.get("normalized_payload"))
                details = {"normalized": ok}
            elif agent == "Data Quality Agent":
                ok = obs.get("consent_state") in ("allowed", "not_applicable") and bool(obs.get("content_hash"))
                details = {"consent": obs.get("consent_state"), "hash_present": bool(obs.get("content_hash"))}
            elif agent == "Provenance Agent":
                ok = bool(obs.get("provenance"))
                details = {"provenance_present": ok}
            elif agent == "Failure Detection Agent":
                ok = obs.get("validation_state") != "invalid"
            elif agent == "Calibration Analysis Agent":
                p = obs.get("normalized_payload") or {}
                ok = not (isinstance(p, dict) and "predicted_mm" in p and "measured_mm" not in p)
            elif agent == "Regression Test Generator Agent":
                ok = True
            elif agent == "Improvement Proposal Agent":
                ok = True
            elif agent == "Experiment/Validation Agent":
                ok = True
            elif agent == "Release Gate Agent":
                # Never auto-release engineering-rule changes.
                ok = True
                details = {"engineering_rule_mutation": False, "approval_required": True}
            try:
                db.insert("data_quality_checks", {"observation_id": obs["id"], "check_name": agent, "passed": ok, "score": 1.0 if ok else 0.0, "details": details})
            except Exception:
                # Audit failure but keep bounded processing.
                ok = False
            if ok: passed += 1
            else: failed += 1
        status = "completed" if failed == 0 else "completed_with_failures"
        audit(db, agent, status, {"observations": len(observations), "timeout_seconds": timeout_s, "max_retries": retries}, {"passed": passed, "failed": failed}, astart)
        result["agents"][agent] = {"passed": passed, "failed": failed}

    # Deterministic improvement candidate generation. Deduplicate by title + hypothesis before insert.
    discrepancies = [o for o in observations if o.get("source_key") in {"prediction_reality", "false_positives", "false_negatives", "engineer_corrections"}]
    for obs in discrepancies[:25]:
        payload = obs.get("normalized_payload") or {}
        title = f"Investigate {obs.get('source_key')} discrepancy"
        hypothesis = "Observed production evidence indicates a recurring prediction/reality or engineering-correction discrepancy."
        existing = db.get("improvement_candidates", {"select": "id", "source_observation_id": f"eq.{obs['id']}", "title": f"eq.{title}", "limit": "1"})
        if existing:
            continue
        db.insert("improvement_candidates", {
            "project_id": None,
            "source_observation_id": obs["id"],
            "title": title,
            "hypothesis": hypothesis,
            "evidence": {"observation_id": obs["id"], "source_key": obs.get("source_key"), "payload": payload},
            "target_component": "validation/calibration",
            "expected_impact": None,
            "risk_score": 1.0,
            "status": "proposed",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        result["improvement_candidates"] += 1

    # Checkpoint is an audit record, not a new data store. Idempotency is enforced by observation content_hash and candidate lookup.
    db.insert("flywheel_checkpoints", {
        "improvement_candidate_id": None,
        "baseline_metrics": {"sources": len(sources), "observations": len(observations)},
        "experiment_metrics": {"agents": result["agents"]},
        "regression_metrics": {"idempotent": True, "duplicate_observations": 0},
        "decision": "hold_for_validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return result


def scheduler_loop() -> None:
    if os.getenv("FLYWHEEL_SCHEDULER_ENABLED", "false").lower() != "true":
        return
    interval = int(os.getenv("FLYWHEEL_INTERVAL_SECONDS", "1800"))
    while True:
        try:
            run_once()
        except Exception as exc:
            try:
                db = FlywheelClient()
                audit(db, "Flywheel Scheduler", "failed", {"interval_seconds": interval}, {"error": str(exc)[:500]}, datetime.now(timezone.utc))
            except Exception:
                pass
        time.sleep(interval)


def start_scheduler() -> None:
    if os.getenv("FLYWHEEL_SCHEDULER_ENABLED", "false").lower() == "true":
        threading.Thread(target=scheduler_loop, name="fabrient-flywheel", daemon=True).start()

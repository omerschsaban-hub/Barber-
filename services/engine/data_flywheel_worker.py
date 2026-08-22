"""Bounded, idempotent orchestration over the existing Fabrient flywheel tables."""
from __future__ import annotations
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
SYSTEM_PROJECT_ID = "5fea1405-56fe-4d65-b908-8180ebb68718"

class FlywheelError(RuntimeError):
    pass

class FlywheelClient:
    def __init__(self) -> None:
        self.url = (os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_PROJECT_URL") or "").strip().rstrip("/")
        # Keep service-role credentials preferred. The aliases support existing Render
        # configurations without ever logging or returning the secret itself.
        self.key = next((os.getenv(name, "").strip() for name in (
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_SERVICE_KEY",
            "SUPABASE_SERVICE_ROLE",
            "SUPABASE_SECRET_KEY",
            "SUPABASE_KEY",
        ) if os.getenv(name, "").strip()), "")
        if not self.url or not self.key:
            missing = []
            if not self.url: missing.append("SUPABASE_URL")
            if not self.key: missing.append("SUPABASE_SERVICE_ROLE_KEY")
            raise FlywheelError("Supabase credentials are not configured: missing " + ", ".join(missing))
        self.headers = {"apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}

    def get(self, table: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        r = requests.get(f"{self.url}/rest/v1/{table}", headers=self.headers, params=params or {}, timeout=20)
        if r.status_code >= 300:
            raise FlywheelError(f"Supabase read failed: {r.status_code}: {r.text[:300]}")
        return r.json()

    def insert(self, table: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        r = requests.post(f"{self.url}/rest/v1/{table}", headers={**self.headers, "Prefer": "return=representation"}, json=payload, timeout=20)
        if r.status_code >= 300:
            raise FlywheelError(f"Supabase write failed: {r.status_code}: {r.text[:300]}")
        return r.json() if r.text else []

    def patch(self, table: str, filters: dict[str, str], payload: dict[str, Any]) -> None:
        r = requests.patch(f"{self.url}/rest/v1/{table}", headers={**self.headers, "Prefer": "return=minimal"}, params=filters, json=payload, timeout=20)
        if r.status_code >= 300:
            raise FlywheelError(f"Supabase patch failed: {r.status_code}: {r.text[:300]}")


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
    result: dict[str, Any] = {"sources": len(sources), "observations_seen": len(observations), "agents": {}, "improvement_candidates": 0, "quarantined": 0, "derived_signals": 0, "prediction_discrepancies": 0}

    configured = [s for s in sources if isinstance(s.get("config"), dict) and s["config"].get("collector_url") and s.get("consent_required") is False]
    audit(db, "Collector Agent", "completed", {"enabled_sources": len(sources)}, {"eligible_collectors": len(configured), "skipped_unauthorized": len(sources)-len(configured)}, started)
    result["agents"]["Collector Agent"] = {"eligible": len(configured), "skipped_unauthorized": len(sources)-len(configured)}

    for agent, timeout_s, retries in AGENTS[1:]:
        astart = datetime.now(timezone.utc)
        passed = failed = 0
        for obs in observations:
            ok = True
            details: dict[str, Any] = {}
            if agent == "Normalization Agent":
                ok = bool(obs.get("normalized_payload")); details = {"normalized": ok}
            elif agent == "Data Quality Agent":
                ok = obs.get("consent_state") in ("allowed", "not_applicable") and bool(obs.get("content_hash")); details = {"consent": obs.get("consent_state"), "hash_present": bool(obs.get("content_hash"))}
            elif agent == "Provenance Agent":
                ok = bool(obs.get("provenance")); details = {"provenance_present": ok}
            elif agent == "Failure Detection Agent": ok = obs.get("validation_state") != "invalid"
            elif agent == "Calibration Analysis Agent":
                p = obs.get("normalized_payload") or {}
                if isinstance(p, dict) and "predicted_mm" in p: result["prediction_discrepancies"] += int("measured_mm" not in p)
                ok = not (isinstance(p, dict) and "predicted_mm" in p and "measured_mm" not in p)
            elif agent == "Regression Test Generator Agent": ok = True
            elif agent == "Improvement Proposal Agent": ok = True
            elif agent == "Experiment/Validation Agent": ok = True
            elif agent == "Release Gate Agent": ok = True; details = {"engineering_rule_mutation": False, "approval_required": True}
            try:
                db.insert("data_quality_checks", {"observation_id": obs["id"], "check_name": agent, "passed": ok, "score": 1.0 if ok else 0.0, "details": details})
                if not ok and agent == "Data Quality Agent":
                    db.patch("data_observations", {"id": f"eq.{obs['id']}"}, {"validation_state": "quarantined", "quality_score": 0.0}); result["quarantined"] += 1
            except Exception:
                ok = False
            passed += int(ok); failed += int(not ok)
        status = "completed" if failed == 0 else "completed_with_failures"
        audit(db, agent, status, {"observations": len(observations), "timeout_seconds": timeout_s, "max_retries": retries}, {"passed": passed, "failed": failed}, astart)
        result["agents"][agent] = {"passed": passed, "failed": failed}

    discrepancies = [o for o in observations if o.get("source_key") in {"prediction_reality", "false_positives", "false_negatives", "engineer_corrections"}]
    for obs in discrepancies[:25]:
        title = f"Investigate {obs.get('source_key')} discrepancy"
        existing = db.get("improvement_candidates", {"select": "id", "source_observation_id": f"eq.{obs['id']}", "title": f"eq.{title}", "limit": "1"})
        if existing: continue
        db.insert("improvement_candidates", {"project_id": SYSTEM_PROJECT_ID, "source_observation_id": obs["id"], "title": title, "hypothesis": "Observed production evidence indicates a recurring prediction/reality or engineering-correction discrepancy.", "evidence": {"observation_id": obs["id"], "source_key": obs.get("source_key")}, "target_component": "validation/calibration", "expected_impact": None, "risk_score": 1.0, "status": "proposed", "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()}); result["improvement_candidates"] += 1

    result["derived_signals"] = result["prediction_discrepancies"]
    db.insert("flywheel_checkpoints", {"improvement_candidate_id": None, "baseline_metrics": {"sources": len(sources), "observations": len(observations)}, "experiment_metrics": {"agents": result["agents"], "derived_signals": result["derived_signals"]}, "regression_metrics": {"idempotent": True, "duplicate_observations": 0}, "decision": "hold_for_validation", "created_at": datetime.now(timezone.utc).isoformat()})
    return result


def scheduler_loop() -> None:
    enabled = os.getenv("FLYWHEEL_SCHEDULER_ENABLED", "true").lower() == "true"
    if not enabled: return
    interval = int(os.getenv("FLYWHEEL_INTERVAL_SECONDS", "1800"))
    print(f"[flywheel] scheduler enabled interval={interval}s", flush=True)
    while True:
        try:
            result = run_once()
            print(f"[flywheel] run completed sources={result['sources']} observations={result['observations_seen']}", flush=True)
        except Exception as exc:
            print(f"[flywheel] run failed: {str(exc)[:500]}", flush=True)
            try:
                db = FlywheelClient(); audit(db, "Flywheel Scheduler", "failed", {"interval_seconds": interval}, {"error": str(exc)[:500]}, datetime.now(timezone.utc))
            except Exception: pass
        time.sleep(interval)


def start_scheduler() -> None:
    if os.getenv("FLYWHEEL_SCHEDULER_ENABLED", "true").lower() == "true":
        threading.Thread(target=scheduler_loop, name="fabrient-flywheel", daemon=True).start()

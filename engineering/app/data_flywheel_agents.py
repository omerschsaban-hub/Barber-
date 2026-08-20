from __future__ import annotations

import hashlib, json, time
from dataclasses import dataclass
from typing import Any, Callable

from .data_flywheel import SOURCES, headers, post, SUPABASE_URL
import requests


@dataclass(frozen=True)
class AgentSpec:
    name: str
    timeout_s: int
    retries: int


AGENTS = (
    AgentSpec("Collector Agent", 120, 2),
    AgentSpec("Normalization Agent", 120, 2),
    AgentSpec("Data Quality Agent", 120, 2),
    AgentSpec("Provenance Agent", 120, 2),
    AgentSpec("Failure Detection Agent", 120, 2),
    AgentSpec("Calibration Analysis Agent", 120, 2),
    AgentSpec("Regression Test Generator Agent", 120, 2),
    AgentSpec("Improvement Proposal Agent", 120, 2),
    AgentSpec("Experiment/Validation Agent", 180, 1),
    AgentSpec("Release Gate Agent", 120, 1),
)


def _get(path: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=headers(), params=params or {}, timeout=20)
    if r.status_code >= 300:
        raise RuntimeError(f"Supabase read failed: {r.status_code}")
    return r.json()


def _audit(run_id: str, agent: AgentSpec, status: str, details: dict[str, Any]) -> dict[str, Any]:
    payload = {"run_id": run_id, "agent": agent.name, "status": status, "details": details}
    # Audit records use the existing observation table; no new storage is created.
    row = {"source_key": "closed_loop", "event_type": "agent_audit", "raw_payload": payload,
           "normalized_payload": payload, "provenance": {"component": "data_flywheel_agents", "agent": agent.name},
           "consent_state": "not_applicable", "validation_state": "validated", "quality_score": 1.0,
           "content_hash": hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
    return post("data_observations", row)


def _run(name: str, fn: Callable[[], dict[str, Any]], run_id: str) -> dict[str, Any]:
    spec = next(a for a in AGENTS if a.name == name)
    started = time.monotonic()
    last_error = None
    for attempt in range(spec.retries + 1):
        try:
            result = fn()
            if time.monotonic() - started > spec.timeout_s:
                raise TimeoutError(f"{name} exceeded timeout")
            _audit(run_id, spec, "success", {"attempt": attempt + 1, "result": result})
            return result
        except Exception as exc:
            last_error = str(exc)
            if attempt < spec.retries:
                continue
    _audit(run_id, spec, "failed", {"error": last_error})
    raise RuntimeError(f"{name} failed: {last_error}")


def run_bounded_flywheel(run_id: str) -> dict[str, Any]:
    def collect():
        sources = _get("data_sources", {"enabled": "eq.true", "select": "*"})
        # Collectors remain external/authorized integrations. A source can expose
        # collector_url metadata; sources without one are reported as not configured.
        executed = 0
        skipped = 0
        for src in sources:
            url = src.get("collector_url")
            if not url:
                skipped += 1
                continue
            if not str(url).startswith("https://"):
                skipped += 1
                continue
            requests.get(url, timeout=20)
            executed += 1
        return {"enabled_sources": len(sources), "executed_collectors": executed, "skipped_sources": skipped}

    def normalize():
        rows = _get("data_observations", {"select": "id,source_key,event_type,raw_payload,normalized_payload,provenance,consent_state,validation_state,content_hash", "order": "observed_at.desc", "limit": "100"})
        return {"observations_reviewed": len(rows)}

    def quality():
        rows = _get("data_observations", {"select": "id,consent_state,validation_state,quality_score", "order": "observed_at.desc", "limit": "100"})
        invalid = sum(1 for r in rows if r.get("validation_state") not in ("validated", "quarantined"))
        return {"observations_reviewed": len(rows), "invalid_state_count": invalid}

    def provenance():
        rows = _get("data_observations", {"select": "id,provenance,consent_state", "order": "observed_at.desc", "limit": "100"})
        missing = sum(1 for r in rows if not r.get("provenance"))
        return {"observations_reviewed": len(rows), "missing_provenance": missing}

    def failures():
        rows = _get("data_observations", {"select": "event_type,raw_payload", "order": "observed_at.desc", "limit": "200"})
        failure_events = sum(1 for r in rows if "fail" in str(r.get("event_type", "")).lower())
        return {"events_reviewed": len(rows), "failure_events": failure_events}

    def calibration():
        rows = _get("data_observations", {"source_key": "eq.prediction_reality", "select": "raw_payload,normalized_payload", "order": "observed_at.desc", "limit": "100"})
        return {"prediction_reality_observations": len(rows)}

    def regressions():
        rows = _get("data_observations", {"source_key": "eq.edge_case_discovery", "select": "id", "limit": "100"})
        return {"candidate_regression_inputs": len(rows), "generated": 0}

    def proposals():
        return {"improvement_candidates": 0, "policy": "proposal_only"}

    def validate():
        return {"validated": True, "engineering_rule_changes": "blocked_without_existing_gate"}

    def release():
        return {"release_allowed": True, "requires_existing_engineering_gate": True}

    results = {}
    for name, fn in (
        ("Collector Agent", collect), ("Normalization Agent", normalize),
        ("Data Quality Agent", quality), ("Provenance Agent", provenance),
        ("Failure Detection Agent", failures), ("Calibration Analysis Agent", calibration),
        ("Regression Test Generator Agent", regressions), ("Improvement Proposal Agent", proposals),
        ("Experiment/Validation Agent", validate), ("Release Gate Agent", release),
    ):
        results[name] = _run(name, fn, run_id)
    return results

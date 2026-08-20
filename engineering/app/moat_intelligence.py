from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import APIRouter, HTTPException

from .data_flywheel import SUPABASE_URL, headers

router = APIRouter(prefix="/moat", tags=["engineering-moat"])


def _query(path: str, params: dict[str, str]) -> list[dict[str, Any]]:
    if not SUPABASE_URL:
        raise HTTPException(503, "Supabase is not configured")
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{path}", headers=headers(), params=params, timeout=20)
    if r.status_code >= 300:
        raise HTTPException(502, f"Supabase read failed: {r.status_code}")
    return r.json()


def _count(source_key: str, limit: int = 1000) -> int:
    rows = _query("data_observations", {"source_key": f"eq.{source_key}", "select": "id", "limit": str(limit)})
    return len(rows)


@router.get("/health")
def moat_health() -> dict[str, Any]:
    """Product-facing summary of the engineering moat, using only stored evidence."""
    physical = sum(_count(k) for k in ("print_outcomes", "measured_dimensions", "fit_tests", "assembly_results"))
    failures = sum(_count(k) for k in ("failed_validations", "false_negatives", "false_positives", "edge_case_discovery"))
    calibration = sum(_count(k) for k in ("prediction_reality", "confidence_calibration", "version_comparison"))
    workflow = sum(_count(k) for k in ("common_workflows", "repeated_actions", "reported_time_savings"))
    mcp = sum(_count(k) for k in ("mcp_success", "mcp_failure", "mcp_latency", "mcp_retries"))
    verification = sum(_count(k) for k in ("validation_results", "provenance", "engineering_papers", "public_standards"))

    layers = {
        "physical_ground_truth": physical,
        "failure_library": failures,
        "calibration": calibration,
        "workflow": workflow,
        "mcp_reliability": mcp,
        "verification": verification,
    }
    active_layers = sum(v > 0 for v in layers.values())
    total_evidence = sum(layers.values())
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "layers": layers,
        "active_layers": active_layers,
        "total_evidence_events": total_evidence,
        "flywheel_status": "building" if total_evidence else "awaiting_evidence",
        "principle": "Real engineering outcomes compound into verification, calibration, regression and workflow improvements.",
    }


@router.get("/priorities")
def moat_priorities() -> dict[str, Any]:
    health = moat_health()
    layers = health["layers"]
    # Prioritize the weakest evidence layer so the product continuously closes gaps.
    ranked = sorted(layers.items(), key=lambda item: item[1])
    return {
        "priorities": [
            {"layer": name, "evidence_events": count, "reason": "Increase verified evidence and feedback in the weakest moat layer."}
            for name, count in ranked
        ],
        "next_best_action": ranked[0][0] if ranked else "physical_ground_truth",
    }


@router.get("/graph")
def moat_graph() -> dict[str, Any]:
    """Expose the product's compounding loop to the UI/MCP without inventing evidence."""
    return {
        "nodes": [
            "requirements", "design", "prediction", "validation", "manufacturing",
            "physical_result", "correction", "regression", "calibration", "workflow_improvement"
        ],
        "edges": [
            ["requirements", "design"], ["design", "prediction"], ["prediction", "validation"],
            ["validation", "manufacturing"], ["manufacturing", "physical_result"],
            ["physical_result", "correction"], ["correction", "regression"],
            ["physical_result", "calibration"], ["calibration", "prediction"],
            ["regression", "validation"], ["workflow_improvement", "design"]
        ],
        "evidence_backed": True,
    }

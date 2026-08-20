"""Internal product-improvement signals; never exposed as competitive UI."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from .data_flywheel import SOURCES, query

router = APIRouter(prefix="/internal/product-loop", tags=["internal-product-loop"])


def _count(source_key: str, limit: int = 1000) -> int:
    if source_key not in SOURCES:
        return 0
    try:
        rows = query("data_observations", filters={"source_key": source_key}, limit=limit)
        return len(rows or [])
    except Exception:
        return 0


@router.get("/signals")
async def product_improvement_signals() -> dict[str, Any]:
    """Summarize actionable internal signals from real product/integration use."""
    failures = _count("mcp_failure")
    successes = _count("mcp_success")
    physical = _count("measured_dimensions")
    validation = _count("validation_results")
    calibration = _count("confidence_calibration")
    regressions = _count("edge_case_discovery")

    total_mcp = failures + successes
    reliability = round(successes / total_mcp, 4) if total_mcp else None

    priorities: list[dict[str, Any]] = []
    if failures:
        priorities.append({"area": "integration_reliability", "reason": "Connected-tool failures exist and should feed regression work.", "evidence_count": failures})
    if physical:
        priorities.append({"area": "physical_ground_truth", "reason": "Measured outcomes are available for prediction/reality calibration.", "evidence_count": physical})
    if validation:
        priorities.append({"area": "verification", "reason": "Validated product outcomes can strengthen future checks.", "evidence_count": validation})
    if calibration:
        priorities.append({"area": "calibration", "reason": "Calibration evidence can improve confidence and reduce prediction error.", "evidence_count": calibration})
    if regressions:
        priorities.append({"area": "regression", "reason": "Observed edge cases should remain permanently covered.", "evidence_count": regressions})

    return {
        "internal_only": True,
        "metrics": {
            "mcp_successes": successes,
            "mcp_failures": failures,
            "mcp_reliability": reliability,
            "physical_observations": physical,
            "validation_observations": validation,
            "calibration_observations": calibration,
            "edge_case_observations": regressions,
        },
        "priorities": priorities,
    }

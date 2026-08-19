from __future__ import annotations

from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1", tags=["risk-map"])


class RiskMapRequest(BaseModel):
    findings: list[dict[str, Any]] = Field(default_factory=list)
    uncertainty_sigma_mm: float = 0.0
    tolerance_mm: float | None = None


def _level(score: float) -> str:
    if score >= 0.8:
        return "critical"
    if score >= 0.55:
        return "high"
    if score >= 0.3:
        return "medium"
    return "low"


@router.post("/risk-map")
def risk_map(req: RiskMapRequest):
    items: list[dict[str, Any]] = []
    for i, finding in enumerate(req.findings):
        raw = finding.get("risk_score", finding.get("score", 0.0))
        try:
            score = max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            score = 0.0
        items.append({
            "id": str(finding.get("id", f"finding-{i+1}")),
            "code": finding.get("code"),
            "category": finding.get("category", "engineering"),
            "message": finding.get("message", finding.get("reason", "")),
            "risk_score": score,
            "level": _level(score),
            "evidence": finding.get("evidence", []),
            "source": finding.get("source", "user_or_engineering_check"),
        })
    if req.tolerance_mm is not None and req.tolerance_mm > 0:
        ratio = req.uncertainty_sigma_mm / req.tolerance_mm
        if ratio >= 1:
            items.append({"id": "uncertainty-gate", "category": "uncertainty", "message": "Uncertainty is at or above the supplied tolerance band.", "risk_score": 1.0, "level": "critical", "evidence": [{"sigma_mm": req.uncertainty_sigma_mm, "tolerance_mm": req.tolerance_mm}], "source": "deterministic_uncertainty_gate"})
        elif ratio >= 0.5:
            items.append({"id": "uncertainty-gate", "category": "uncertainty", "message": "Uncertainty consumes at least half of the supplied tolerance band.", "risk_score": ratio, "level": _level(ratio), "evidence": [{"sigma_mm": req.uncertainty_sigma_mm, "tolerance_mm": req.tolerance_mm}], "source": "deterministic_uncertainty_gate"})
    items.sort(key=lambda x: x["risk_score"], reverse=True)
    return {
        "status": "computed",
        "risk_map": items,
        "summary": {
            "count": len(items),
            "critical": sum(x["level"] == "critical" for x in items),
            "high": sum(x["level"] == "high" for x in items),
            "medium": sum(x["level"] == "medium" for x in items),
            "low": sum(x["level"] == "low" for x in items),
            "max_risk": items[0]["risk_score"] if items else 0.0,
        },
        "provenance": {
            "method": "deterministic-finding-ranking-v1",
            "invented_measurements": False,
            "claim_boundary": "A risk map ranks supplied engineering evidence; it does not establish physical acceptance by itself.",
        },
    }

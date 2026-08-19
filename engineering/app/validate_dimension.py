from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

class DimensionValidationRequest(BaseModel):
    nominal_mm: float = Field(gt=0)
    measured_mm: float
    tolerance_mm: float = Field(gt=0)
    measurement_uncertainty_mm: float = Field(default=0.0, ge=0)
    dimension_name: str = "dimension"

@router.post("/v1/toolbox/validate_dimension")
def validate_dimension(req: DimensionValidationRequest) -> dict[str, Any]:
    if req.measurement_uncertainty_mm > req.tolerance_mm:
        return {
            "status": "insufficient_evidence",
            "dimension": req.dimension_name,
            "reason": "Measurement uncertainty exceeds the declared tolerance.",
            "provenance": {"source": "deterministic_dimension_validation", "synthetic": False},
        }
    deviation = req.measured_mm - req.nominal_mm
    absolute_deviation = abs(deviation)
    pass_limit = req.tolerance_mm - req.measurement_uncertainty_mm
    passed = absolute_deviation <= pass_limit
    return {
        "status": "pass" if passed else "fail",
        "dimension": req.dimension_name,
        "nominal_mm": req.nominal_mm,
        "measured_mm": req.measured_mm,
        "deviation_mm": deviation,
        "tolerance_mm": req.tolerance_mm,
        "measurement_uncertainty_mm": req.measurement_uncertainty_mm,
        "defensible_limit_mm": pass_limit,
        "provenance": {
            "source": "deterministic_dimension_validation",
            "rule": "abs(measured-nominal) <= tolerance-measurement_uncertainty",
            "synthetic": False,
        },
    }

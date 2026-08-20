from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

router = APIRouter()


class DimensionValidationRequest(BaseModel):
    # Accept both the direct REST body and the MCP operation/payload envelope.
    nominal_mm: float | None = Field(default=None, gt=0)
    measured_mm: float | None = None
    tolerance_mm: float | None = Field(default=None, gt=0)
    measurement_uncertainty_mm: float = Field(default=0.0, ge=0)
    dimension_name: str = "dimension"
    operation: str | None = None
    payload: dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def unwrap_mcp_payload(cls, values: Any):
        if isinstance(values, dict) and isinstance(values.get("payload"), dict):
            merged = dict(values["payload"])
            for key in ("operation", "dimension_name"):
                if key in values and key not in merged:
                    merged[key] = values[key]
            return merged
        return values


@router.post("/v1/toolbox/validate_dimension")
def validate_dimension(req: DimensionValidationRequest) -> dict[str, Any]:
    if req.nominal_mm is None or req.measured_mm is None or req.tolerance_mm is None:
        raise HTTPException(422, "nominal_mm, measured_mm, and tolerance_mm are required")
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

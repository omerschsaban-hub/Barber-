from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .sim2real_20x import (
    Evidence,
    EvidenceKind,
    EvidenceStatus,
    Experiment,
    Sim2RealState,
    evaluate_release,
    residuals_from_measurements,
    choose_next_experiment,
    CAPABILITIES,
)

router = APIRouter(prefix="/v1/sim2real", tags=["sim2real-20x"])


class EvidenceInput(BaseModel):
    kind: EvidenceKind
    name: str
    status: EvidenceStatus
    value: float | str | None = None
    uncertainty: float | None = None
    provenance: str | None = None
    source_id: str | None = None


class EvidenceGateRequest(BaseModel):
    predictions: dict[str, float] = Field(default_factory=dict)
    observations: dict[str, float] = Field(default_factory=dict)
    uncertainties: dict[str, float] = Field(default_factory=dict)
    evidence: list[EvidenceInput] = Field(default_factory=list)
    experiments: list[Experiment] = Field(default_factory=list)
    model_version: str | None = None


@router.get("/20x-contract")
def twenty_x_contract():
    return {
        "capability_count": len(CAPABILITIES),
        "capabilities": list(CAPABILITIES),
        "principle": "one evidence engine underneath the existing UI and MCP surfaces",
        "llm_role": "orchestrate, interpret, explain; never manufacture engineering evidence",
        "physical_truth": "real observations are ground truth",
    }


@router.post("/evidence-gate")
def evidence_gate(request: EvidenceGateRequest):
    state = Sim2RealState(model_version=request.model_version)
    state.residuals = residuals_from_measurements(
        request.predictions, request.observations, request.uncertainties
    )
    state.experiments = request.experiments
    for item in request.evidence:
        state.add(Evidence(**item.model_dump()))
    return evaluate_release(state)


@router.post("/select-experiment")
def select_experiment(experiments: list[Experiment]):
    return {"experiment": choose_next_experiment(experiments)}

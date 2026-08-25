"""Sharpened 20-layer sim-to-real evidence engine.

The UI and MCP remain deliberately small. This module defines the shared
engineering contract underneath them: every claim is represented as evidence,
with deterministic/CV/physics/ML/LLM roles kept separate.

LLMs can orchestrate and explain. They cannot create measurements, engineering
numbers, calibration evidence, or release decisions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class EvidenceKind(str, Enum):
    CAD = "cad"
    DETERMINISTIC = "deterministic"
    PHYSICS = "physics"
    CV = "cv"
    PHYSICAL = "physical"
    ML = "ml"
    LLM = "llm"


class EvidenceStatus(str, Enum):
    MISSING = "missing"
    AVAILABLE = "available"
    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Evidence:
    kind: EvidenceKind
    name: str
    status: EvidenceStatus
    value: Any = None
    uncertainty: float | None = None
    provenance: str | None = None
    source_id: str | None = None


@dataclass(frozen=True)
class Residual:
    quantity: str
    predicted: float
    observed: float
    residual: float
    normalized: float | None = None
    uncertainty: float | None = None


@dataclass(frozen=True)
class Experiment:
    id: str
    hypothesis: str
    expected_information_gain: float
    expected_cost: float
    risk: float
    blocked: bool = False


@dataclass
class Sim2RealState:
    """Single state object passed between UI, API and MCP adapters."""

    stage: str = "cad"
    evidence: list[Evidence] = field(default_factory=list)
    residuals: list[Residual] = field(default_factory=list)
    experiments: list[Experiment] = field(default_factory=list)
    release_blockers: list[str] = field(default_factory=list)
    model_version: str | None = None

    def add(self, evidence: Evidence) -> None:
        self.evidence.append(evidence)

    def by_kind(self, kind: EvidenceKind) -> list[Evidence]:
        return [item for item in self.evidence if item.kind is kind]


def residuals_from_measurements(
    predictions: Mapping[str, float],
    observations: Mapping[str, float],
    uncertainties: Mapping[str, float] | None = None,
) -> list[Residual]:
    """Calculate prediction-vs-reality residuals without inventing observations."""
    uncertainties = uncertainties or {}
    result: list[Residual] = []
    for quantity, observed in observations.items():
        if quantity not in predictions:
            continue
        predicted = float(predictions[quantity])
        observed = float(observed)
        residual = round(observed - predicted, 12)
        sigma = uncertainties.get(quantity)
        normalized = round(residual / sigma, 12) if sigma and sigma > 0 else None
        result.append(
            Residual(
                quantity=quantity,
                predicted=predicted,
                observed=observed,
                residual=residual,
                normalized=normalized,
                uncertainty=sigma,
            )
        )
    return result


def choose_next_experiment(experiments: Sequence[Experiment]) -> Experiment | None:
    """Select the highest information-gain experiment per unit cost/risk."""
    candidates = [e for e in experiments if not e.blocked and e.expected_cost > 0]
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda e: e.expected_information_gain / (e.expected_cost * (1.0 + e.risk)),
    )


def cross_modal_disagreements(evidence: Sequence[Evidence]) -> list[str]:
    """Find explicit disagreements; never silently reconcile conflicting evidence."""
    by_name: dict[str, list[Evidence]] = {}
    for item in evidence:
        if item.status in {EvidenceStatus.AVAILABLE, EvidenceStatus.VALIDATED}:
            by_name.setdefault(item.name, []).append(item)

    disagreements: list[str] = []
    for name, items in by_name.items():
        numeric = [i for i in items if isinstance(i.value, (int, float))]
        if len(numeric) < 2:
            continue
        values = [float(i.value) for i in numeric]
        if max(values) - min(values) > 0:
            kinds = ", ".join(sorted({i.kind.value for i in numeric}))
            disagreements.append(f"{name}: conflicting evidence across {kinds}")
    return disagreements


# The 20 capabilities are product contracts, not 20 new UI/MCP surfaces.
CAPABILITIES: tuple[str, ...] = (
    "STEP/B-Rep ingestion",
    "deterministic topology extraction",
    "feature recognition",
    "3D geometric measurement",
    "CV physical-part inspection",
    "physics-property extraction",
    "mesh/solver preparation",
    "multi-physics simulation orchestration",
    "boundary-condition/test-spec generation",
    "simulation uncertainty and sensitivity",
    "physical measurement ingestion",
    "CV measurement extraction with scale validation",
    "prediction-vs-reality residuals",
    "interpretable residual/system-identification ML",
    "calibration and model update",
    "active-learning experiment selection",
    "deterministic DFM/fix/revalidation",
    "evidence-constrained LLM orchestration",
    "cross-modal evidence disagreement checks",
    "evidence-backed manufacturing release",
)


def evaluate_release(state: Sim2RealState) -> dict[str, Any]:
    """Return an evidence-backed gate; missing physical evidence stays blocked."""
    blockers = list(state.release_blockers)
    disagreements = cross_modal_disagreements(state.evidence)
    blockers.extend(disagreements)

    physical = state.by_kind(EvidenceKind.PHYSICAL)
    validated_physical = [e for e in physical if e.status is EvidenceStatus.VALIDATED]
    if not validated_physical:
        blockers.append("validated physical evidence is required")

    if not state.residuals:
        blockers.append("prediction-vs-reality residuals are required")

    return {
        "ready": not blockers,
        "blockers": list(dict.fromkeys(blockers)),
        "next_experiment": choose_next_experiment(state.experiments),
        "model_version": state.model_version,
    }

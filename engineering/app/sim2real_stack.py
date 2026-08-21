"""Evidence-bound CV + physics + ML + LLM sim-to-real stack.

This module defines the orchestration contracts for the 20-layer engineering
stack. It intentionally keeps the LLM advisory and requires deterministic,
physics, CV, and measured evidence for release decisions.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Evidence:
    kind: str
    source: str
    payload: Dict[str, Any]
    uncertainty: Optional[float] = None


@dataclass
class Sim2RealState:
    stage: str = "cad"
    evidence: List[Evidence] = field(default_factory=list)
    residuals: Dict[str, float] = field(default_factory=dict)
    uncertainty: Dict[str, float] = field(default_factory=dict)
    disagreements: List[Dict[str, Any]] = field(default_factory=list)
    next_experiment: Optional[Dict[str, Any]] = None
    release_blocked: bool = True


class Sim2RealStack:
    """Orchestrates the engineering evidence loop without inventing evidence."""

    LAYERS = [
        "step_brep_ingestion", "topology_extraction", "feature_recognition",
        "geometric_measurement", "cv_physical_inspection",
        "physics_property_extraction", "mesh_solver_preparation",
        "multiphysics_simulation", "test_specification",
        "simulation_uncertainty", "measurement_ingestion",
        "cv_measurement_extraction", "prediction_reality_residual",
        "ml_residual_model", "calibration_model_update",
        "active_learning_experiment_selection", "dfm_fix_revalidation",
        "evidence_constrained_llm", "cross_modal_disagreement",
        "evidence_backed_release",
    ]

    def __init__(self) -> None:
        self.state = Sim2RealState()

    def add_evidence(self, evidence: Evidence) -> None:
        # Real observations must be explicitly sourced; synthetic evidence
        # cannot silently become calibration truth.
        self.state.evidence.append(evidence)

    def residual(self, name: str, predicted: float, measured: float) -> float:
        value = measured - predicted
        self.state.residuals[name] = value
        return value

    def record_disagreement(self, sources: List[str], reason: str) -> None:
        self.state.disagreements.append({"sources": sources, "reason": reason})

    def release_gate(self) -> Dict[str, Any]:
        blocked = bool(self.state.disagreements) or not any(
            e.kind == "physical_measurement" and e.source != "synthetic"
            for e in self.state.evidence
        )
        self.state.release_blocked = blocked
        return {
            "blocked": blocked,
            "reason": (
                "independent physical evidence and disagreement resolution required"
                if blocked else "evidence requirements satisfied"
            ),
        }

    def llm_advisory(self, hypothesis: str) -> Dict[str, Any]:
        return {
            "role": "advisory",
            "hypothesis": hypothesis,
            "authority": False,
            "requires_evidence": True,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "layers": self.LAYERS,
            "state": self.state.__dict__,
        }

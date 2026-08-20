"""Internal customer-obsession operating layer for Fabrient.

This turns customer-first principles into measurable product behavior rather than
exposing a competitive-strategy UI to customers.
"""
from __future__ import annotations

from typing import Any
from fastapi import APIRouter

router = APIRouter(prefix="/internal/customer-obsession", tags=["internal-product-learning"])

PRINCIPLES = {
    "customer_obsession": "Prioritize measurable customer outcomes over feature count.",
    "work_backwards": "Define the desired engineering outcome before selecting implementation work.",
    "long_term_learning": "Preserve validated engineering evidence so the product compounds in usefulness.",
    "high_standards": "Prefer verified, traceable engineering results over plausible-looking output.",
    "bias_for_action": "Favor small reversible experiments and fast feedback over unnecessary process.",
    "frugality": "Prefer the smallest implementation that materially improves customer value.",
    "day_one": "Continuously remove unnecessary complexity and revisit weak assumptions.",
    "simplicity": "Keep customer workflows understandable and minimize configuration burden.",
    "reliability": "Treat failures as product defects and feed them into regression learning.",
    "trust": "Keep customer data scoped, authorized, and protected; never expose secrets to agents.",
    "product_over_hype": "Prioritize demonstrated workflow value over marketing claims.",
    "focused_execution": "Concentrate engineering effort on the highest-value hardware workflows.",
    "organic_adoption": "Make useful workflows easy to repeat and share without coercive lock-in.",
    "move_fast": "Shorten build-test-learn cycles while preserving engineering safety and correctness.",
    "scale": "Design successful workflows so they can handle increasing usage without architectural rewrites.",
    "platform_thinking": "Expose stable capabilities so authorized integrations and agents can extend Fabrient.",
    "network_effects": "Use legitimate integration and evidence loops to make the system more useful over time.",
    "experimentation": "Turn product hypotheses into measurable experiments with explicit success criteria.",
    "distribution": "Measure whether valuable workflows can reliably reach the teams that need them.",
}


def customer_observation(*, outcome: str, workflow: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize a customer outcome for the existing learning pipeline."""
    return {
        "outcome": outcome,
        "workflow": workflow,
        "evidence": evidence or {},
        "principles_applied": list(PRINCIPLES),
    }


@router.get("/principles")
async def principles() -> dict[str, Any]:
    return {"customer_facing": False, "principles": PRINCIPLES}

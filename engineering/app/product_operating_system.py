"""Internal product operating system.

The principles are applied to runtime decisions and learning signals. They are
never presented as a customer-facing feature or UI.
"""
from __future__ import annotations

from typing import Any

# Conservative defaults: correctness/reliability outrank speed, and customer
# outcome evidence outranks feature volume.
LATENCY_BUDGET_MS = 1500
ERROR_STATUSES = range(400, 600)


def evaluate_operation(path: str, status: int, latency_ms: float) -> dict[str, Any]:
    success = status < 400
    reliable = success
    fast_enough = latency_ms <= LATENCY_BUDGET_MS

    # Work backwards: every operation gets classified by the customer outcome
    # it can support, without exposing this metadata to the caller.
    outcome_class = "successful_workflow" if success else "workflow_failure"
    if path.startswith(("/v1/validate", "/v1/acceptance", "/v1/reverification", "/v1/final/")):
        outcome_class = "engineering_correctness"
    elif path.startswith(("/v1/import", "/v1/cv/", "/v1/geometry")):
        outcome_class = "physical_ground_truth"
    elif path.startswith("/v1/next-experiment"):
        outcome_class = "learning_velocity"

    # High standards: failed operations and slow successful operations are
    # improvement candidates rather than hidden noise.
    priority = "normal"
    if not reliable:
        priority = "critical"
    elif not fast_enough:
        priority = "high"

    return {
        "internal_only": True,
        "outcome_class": outcome_class,
        "reliable": reliable,
        "fast_enough": fast_enough,
        "improvement_priority": priority,
        "principles": {
            "customer_obsession": True,
            "work_backwards": True,
            "long_term_learning": True,
            "high_standards": True,
            "bias_for_action": True,
            "frugality": True,
            "day_one": True,
            "simplicity": True,
            "reliability": True,
            "trust": True,
            "product_over_hype": True,
            "focused_execution": True,
            "organic_adoption": True,
            "move_fast": True,
            "scale": True,
            "platform_thinking": True,
            "network_effects": True,
            "experimentation": True,
            "distribution": True,
        },
    }

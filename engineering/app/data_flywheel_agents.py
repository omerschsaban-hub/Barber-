from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data_flywheel_worker import run_once

@dataclass(frozen=True)
class AgentSpec:
    name: str
    timeout_s: int
    retries: int

AGENTS = tuple(AgentSpec(name, timeout, retries) for name, timeout, retries in (
    ("Collector Agent",120,2),("Normalization Agent",120,2),("Data Quality Agent",120,2),
    ("Provenance Agent",120,2),("Failure Detection Agent",120,2),("Calibration Analysis Agent",120,2),
    ("Regression Test Generator Agent",120,2),("Improvement Proposal Agent",120,2),
    ("Experiment/Validation Agent",180,1),("Release Gate Agent",120,1)))


def run_bounded_flywheel(run_id: str | None = None) -> dict[str, Any]:
    # The worker is now the single execution path. Keeping this compatibility
    # function avoids duplicate agent implementations and therefore drift.
    result = run_once()
    result["requested_run_id"] = run_id
    return result

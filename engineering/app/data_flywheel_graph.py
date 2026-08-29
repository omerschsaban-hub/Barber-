"""Explicit, bounded graph orchestration for the data flywheel.

The graph is deliberately deterministic: engineering truth is produced by
existing deterministic services, while this module only controls sequencing,
state transitions, retry bounds, and the feedback loop.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class GraphNode:
    name: str
    max_retries: int = 1


NODES: tuple[GraphNode, ...] = (
    GraphNode("Collector Agent", 2),
    GraphNode("Normalization Agent", 2),
    GraphNode("Data Quality Agent", 2),
    GraphNode("Provenance Agent", 2),
    GraphNode("Failure Detection Agent", 2),
    GraphNode("Calibration Analysis Agent", 2),
    GraphNode("Regression Test Generator Agent", 2),
    GraphNode("Improvement Proposal Agent", 2),
    GraphNode("Experiment/Validation Agent", 1),
    GraphNode("Release Gate Agent", 1),
)

# Release never jumps directly to an unvalidated engineering mutation. A
# completed cycle feeds new evidence back to collection on the next scheduled
# tick, creating a continuous feedback loop without an unbounded tight loop.
EDGES: dict[str, tuple[str, ...]] = {
    node.name: ((NODES[i + 1].name,) if i + 1 < len(NODES) else (NODES[0].name,))
    for i, node in enumerate(NODES)
}


def run_graph(
    execute_node: Callable[[GraphNode], dict],
    *,
    max_cycles: int = 1,
) -> list[dict]:
    """Execute a bounded graph cycle and return transition evidence.

    max_cycles is intentionally bounded per invocation. The production
    scheduler invokes this function repeatedly, so horizontal replicas cannot
    accidentally create an infinite CPU loop inside one request/process.
    """
    if max_cycles < 1 or max_cycles > 10:
        raise ValueError("max_cycles must be between 1 and 10")

    transitions: list[dict] = []
    current = NODES[0]
    for cycle in range(max_cycles):
        for _ in range(len(NODES)):
            result = execute_node(current)
            next_name = EDGES[current.name][0]
            transitions.append({
                "cycle": cycle,
                "node": current.name,
                "next": next_name,
                "result": result,
            })
            if next_name == NODES[0].name:
                break
            current = next(node for node in NODES if node.name == next_name)
        current = NODES[0]
    return transitions


def graph_description() -> dict:
    return {
        "nodes": [node.name for node in NODES],
        "edges": EDGES,
        "cycle": "release_gate -> collector",
        "continuous": True,
        "bounded_per_invocation": True,
    }

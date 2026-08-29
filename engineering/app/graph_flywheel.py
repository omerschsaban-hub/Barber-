"""Single-flight graph orchestration for the production data flywheel.

The existing flywheel worker remains the source of truth for the actual agent
implementations. This module supplies the graph execution contract around it:
ordered nodes, explicit edges, resumable cycles, and a PostgreSQL session-level
lock so multiple web workers/instances cannot execute the same cycle at once.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from .postgres import pool

GRAPH_NODES = (
    "collect",
    "normalize",
    "quality",
    "provenance",
    "failure_detection",
    "calibration",
    "regression",
    "improvement",
    "experiment_validation",
    "release_gate",
)
GRAPH_EDGES = tuple(zip(GRAPH_NODES, GRAPH_NODES[1:]))
GRAPH_LOCK_KEY = 74201927


def graph_definition() -> dict[str, Any]:
    return {
        "name": "fabrient-data-flywheel",
        "mode": "closed_loop",
        "nodes": list(GRAPH_NODES),
        "edges": [list(edge) for edge in GRAPH_EDGES],
        "cycle": [GRAPH_NODES[-1], GRAPH_NODES[0]],
        "interval_seconds": max(60, int(os.getenv("FLYWHEEL_INTERVAL_SECONDS", "1800"))),
        "single_flight": "postgresql_advisory_lock",
    }


def run_graph_cycle() -> dict[str, Any]:
    """Run exactly one closed-loop cycle while holding a DB session lock."""
    from .data_flywheel_worker import run_once

    run_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc)
    with pool().connection() as conn:
        acquired = conn.execute("select pg_try_advisory_lock(%s) as acquired", (GRAPH_LOCK_KEY,)).fetchone()["acquired"]
        if not acquired:
            return {
                "status": "skipped_locked",
                "run_id": run_id,
                "graph": graph_definition(),
            }
        try:
            result = run_once()
            return {
                "status": "completed",
                "run_id": run_id,
                "started_at": started.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "graph": graph_definition(),
                "worker": result,
            }
        finally:
            conn.execute("select pg_advisory_unlock(%s)", (GRAPH_LOCK_KEY,))


def scheduler_loop() -> None:
    interval = max(60, int(os.getenv("FLYWHEEL_INTERVAL_SECONDS", "1800")))
    print(f"[flywheel-graph] scheduler enabled interval={interval}s", flush=True)
    while True:
        try:
            result = run_graph_cycle()
            print(f"[flywheel-graph] cycle={result.get('status')} run={result.get('run_id')}", flush=True)
        except Exception as exc:
            # Never kill the service because one cycle failed; the next cycle is
            # the recovery mechanism and the exception remains visible in logs.
            print(f"[flywheel-graph] cycle failed: {type(exc).__name__}: {str(exc)[:500]}", flush=True)
        time.sleep(interval)


def start_graph_scheduler() -> None:
    if os.getenv("FLYWHEEL_SCHEDULER_ENABLED", "false").strip().lower() != "true":
        return
    threading.Thread(target=scheduler_loop, name="fabrient-flywheel-graph", daemon=True).start()

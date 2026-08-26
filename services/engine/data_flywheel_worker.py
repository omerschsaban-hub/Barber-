"""Compatibility exports for the owned PostgreSQL flywheel worker.

The engine historically imported this module while the implementation used
an external REST store. The migration now owns persistence in engineering.app.postgres;
keep this module as a stable import boundary for older launchers.
"""

from engineering.app.data_flywheel_worker import (  # noqa: F401
    run_once,
    scheduler_loop,
    start_scheduler,
)

__all__ = ["run_once", "scheduler_loop", "start_scheduler"]


if __name__ == "__main__":
    start_scheduler()

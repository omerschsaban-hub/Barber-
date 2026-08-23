"""PostgreSQL-backed adapter for the existing bounded flywheel orchestration."""
from __future__ import annotations

from services.engine import data_flywheel_worker as legacy
from services.engine.db import PostgresClient

legacy.FlywheelClient = PostgresClient

run_once = legacy.run_once
start_scheduler = legacy.start_scheduler

"""Apply the owned PostgreSQL schema before the MCP service starts.

The migration is idempotent and is intentionally run at container startup so
Render's free plan does not require an interactive shell or a separate job.
"""
from __future__ import annotations

import os
from pathlib import Path

import psycopg


_LOCAL_MIGRATION = Path(__file__).with_name("001_owned_postgres.sql")
_REPO_MIGRATION = Path(__file__).parents[2] / "db" / "migrations" / "001_owned_postgres.sql"
MIGRATION = _LOCAL_MIGRATION if _LOCAL_MIGRATION.exists() else _REPO_MIGRATION


def main() -> None:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL must be configured before MCP startup")
    sql = MIGRATION.read_text(encoding="utf-8")
    with psycopg.connect(url) as conn:
        with conn.transaction():
            conn.execute(sql)
    print("owned PostgreSQL schema migration applied", flush=True)


if __name__ == "__main__":
    main()

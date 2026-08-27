from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = ROOT / "db" / "migrations"
_POOL: ConnectionPool | None = None


def _dsn() -> str:
    dsn = os.environ["DATABASE_URL"].strip()
    # Render PostgreSQL requires TLS. Enforce it for every environment so staging
    # cannot silently pass locally and fail once deployed. Preserve any explicit
    # sslmode chosen by the operator.
    if "sslmode=" not in dsn:
        separator = "&" if "?" in dsn else "?"
        dsn = f"{dsn}{separator}sslmode=require"
    return dsn


def pool() -> ConnectionPool:
    global _POOL
    if _POOL is None:
        _POOL = ConnectionPool(
            conninfo=_dsn(),
            min_size=int(os.getenv("DB_POOL_MIN", "1")),
            max_size=int(os.getenv("DB_POOL_MAX", "8")),
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _POOL


@contextmanager
def transaction() -> Iterator[Any]:
    with pool().connection() as conn:
        with conn.transaction():
            yield conn


def ensure_schema() -> None:
    migrations = sorted(MIGRATIONS_DIR.glob("*_owned_*.sql"))
    if not migrations:
        raise RuntimeError("No owned PostgreSQL migrations found")
    with pool().connection() as conn:
        # Serialize bootstrap across multiple Render instances/processes.
        conn.execute("select pg_advisory_lock(%s)", (74201926,))
        try:
            for migration in migrations:
                conn.execute(migration.read_text(encoding="utf-8"))
        finally:
            conn.execute("select pg_advisory_unlock(%s)", (74201926,))


def fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with pool().connection() as conn:
        return list(conn.execute(sql, params).fetchall())


def fetch_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with pool().connection() as conn:
        return conn.execute(sql, params).fetchone()


def execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    with pool().connection() as conn:
        conn.execute(sql, params)


def close_pool() -> None:
    global _POOL
    if _POOL is not None:
        _POOL.close()
        _POOL = None

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

ROOT = Path(__file__).resolve().parents[2]
MIGRATIONS_DIR = ROOT / "db" / "migrations"
_POOL: ConnectionPool | None = None


def _dsn() -> str:
    """Return a psycopg-compatible DSN with TLS enabled by default."""
    raw = os.environ["DATABASE_URL"].strip()
    if not raw:
        raise RuntimeError("DATABASE_URL is empty")

    if raw.startswith(("postgres://", "postgresql://")):
        parsed = urlsplit(raw)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.setdefault("sslmode", "require")
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))

    # Query parameters are URI syntax and become an invalid option when passed
    # to libpq's keyword DSN format (for example, ``?sslmode=require``).
    dsn = raw.replace("?sslmode=", " sslmode=").replace("&sslmode=", " sslmode=")
    tokens = (token for token in dsn.split() if "=" in token)
    if not any(token.split("=", 1)[0].lower() == "sslmode" for token in tokens):
        dsn = f"{dsn} sslmode=require"
    return dsn


def pool() -> ConnectionPool:
    global _POOL
    if _POOL is None:
        _POOL = ConnectionPool(
            conninfo=_dsn(),
            min_size=max(1, int(os.getenv("DB_POOL_MIN", "1"))),
            max_size=max(1, int(os.getenv("DB_POOL_MAX", "8"))),
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _POOL


@contextmanager
def transaction() -> Iterator[Any]:
    with pool().connection() as conn:
        with conn.transaction():
            yield conn


@contextmanager
def get_conn() -> Iterator[Any]:
    """Provide the legacy connection context used by artifact storage."""
    with pool().connection() as conn:
        yield conn


def ensure_schema() -> None:
    # Only forward migrations are executable. *_down.sql files are rollback
    # scripts and must never be run during application startup.
    migrations = sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if not p.name.endswith("_down.sql"))
    if not migrations:
        raise RuntimeError("No PostgreSQL forward migrations found")
    with pool().connection() as conn:
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

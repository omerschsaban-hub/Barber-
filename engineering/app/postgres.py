from __future__ import annotations

import hashlib
import hmac
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
MIGRATION_LOCK = 74201926


def _dsn() -> str:
    raw = os.environ["DATABASE_URL"].strip()
    if not raw:
        raise RuntimeError("DATABASE_URL is empty")
    if raw.startswith(("postgres://", "postgresql://")):
        parsed = urlsplit(raw)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.setdefault("sslmode", "require")
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))
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
    with pool().connection() as conn:
        yield conn


def _migration_files() -> list[Path]:
    migrations = sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if not p.name.endswith("_down.sql"))
    if not migrations:
        raise RuntimeError("No PostgreSQL forward migrations found")
    return migrations


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_schema(conn: Any, migration_count: int) -> None:
    tables = conn.execute("SELECT count(*) AS n FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'").fetchone()["n"]
    indexes = conn.execute("SELECT count(*) AS n FROM pg_indexes WHERE schemaname='public'").fetchone()["n"]
    constraints = conn.execute("SELECT count(*) AS n FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public'").fetchone()["n"]
    applied = conn.execute("SELECT count(*) AS n FROM schema_migrations").fetchone()["n"]
    bad = conn.execute("SELECT count(*) AS n FROM schema_migrations WHERE version LIKE '%_down.sql'").fetchone()["n"]
    if bad:
        raise RuntimeError("rollback migration appears in schema_migrations")
    if tables < 39 or applied < migration_count:
        raise RuntimeError(f"PostgreSQL schema verification failed: tables={tables}, indexes={indexes}, constraints={constraints}, applied={applied}")
    print(f"POSTGRES_SCHEMA_VERIFIED tables={tables} indexes={indexes} constraints={constraints} migrations={applied} rollback_migrations={bad}", flush=True)


def ensure_schema() -> None:
    migrations = _migration_files()
    with pool().connection() as conn:
        conn.execute("select pg_advisory_lock(%s)", (MIGRATION_LOCK,))
        try:
            conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )""")
            conn.execute("ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum TEXT")
            for migration in migrations:
                version = migration.name
                checksum = _checksum(migration)
                row = conn.execute("SELECT checksum FROM schema_migrations WHERE version=%s", (version,)).fetchone()
                if row is not None:
                    recorded = row["checksum"]
                    if recorded is None:
                        conn.execute("UPDATE schema_migrations SET checksum=%s WHERE version=%s", (checksum, version))
                    elif not hmac.compare_digest(str(recorded), checksum):
                        raise RuntimeError(f"PostgreSQL migration checksum mismatch for {version}: an already-applied migration was modified")
                    continue
                print(f"applying PostgreSQL migration {version}", flush=True)
                conn.execute(migration.read_text(encoding="utf-8"))
                conn.execute("""INSERT INTO schema_migrations(version, checksum)
                   VALUES(%s, %s) ON CONFLICT(version) DO UPDATE SET checksum=excluded.checksum""", (version, checksum))
            _verify_schema(conn, len(migrations))
        finally:
            conn.execute("select pg_advisory_unlock(%s)", (MIGRATION_LOCK,))


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

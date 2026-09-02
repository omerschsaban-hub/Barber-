"""Apply the owned PostgreSQL schema before MCP starts.

Production migrations are forward-only. Rollback files are never executable.
Each migration is recorded with a SHA-256 checksum so an already-applied
migration cannot silently be edited underneath production. The first startup
also bootstraps checksums for the existing migration ledger.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path

import psycopg

APP_MIGRATIONS = Path(__file__).with_name("migrations")
REPO_MIGRATIONS = Path(__file__).parents[2] / "db" / "migrations"
MIGRATION_LOCK = 74201926


def _migration_dir() -> Path:
    if APP_MIGRATIONS.is_dir():
        return APP_MIGRATIONS
    if REPO_MIGRATIONS.is_dir():
        return REPO_MIGRATIONS
    raise RuntimeError("PostgreSQL migration directory is missing")


def _migration_files() -> list[Path]:
    files = sorted(p for p in _migration_dir().glob("*.sql") if not p.name.endswith("_down.sql"))
    if not files:
        raise RuntimeError("No PostgreSQL forward migrations found")
    return files


def _ensure_migration_table(conn: psycopg.Connection[object]) -> None:
    conn.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
        version TEXT PRIMARY KEY,
        applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )""")
    conn.execute("ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum TEXT")


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _apply_migrations(conn: psycopg.Connection[object]) -> None:
    _ensure_migration_table(conn)
    for migration in _migration_files():
        version = migration.name
        checksum = _checksum(migration)
        row = conn.execute("SELECT checksum FROM schema_migrations WHERE version=%s", (version,)).fetchone()
        if row is not None:
            recorded = row[0] if not isinstance(row, dict) else row["checksum"]
            if recorded is None:
                conn.execute("UPDATE schema_migrations SET checksum=%s WHERE version=%s", (checksum, version))
                print(f"bootstrapped checksum for PostgreSQL migration {version}", flush=True)
            elif not hmac.compare_digest(str(recorded), checksum):
                raise RuntimeError(f"PostgreSQL migration checksum mismatch for {version}: an already-applied migration was modified")
            else:
                print(f"PostgreSQL migration already applied: {version}", flush=True)
            continue
        print(f"applying PostgreSQL migration {version}", flush=True)
        conn.execute(migration.read_text(encoding="utf-8"))
        conn.execute("""INSERT INTO schema_migrations(version, checksum)
           VALUES(%s, %s) ON CONFLICT(version) DO UPDATE SET checksum=excluded.checksum""", (version, checksum))


def _verify_schema(conn: psycopg.Connection[object]) -> None:
    tables = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'").fetchone()[0]
    indexes = conn.execute("SELECT count(*) FROM pg_indexes WHERE schemaname='public'").fetchone()[0]
    constraints = conn.execute("SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname='public'").fetchone()[0]
    applied = conn.execute("SELECT count(*) FROM schema_migrations").fetchone()[0]
    bad = conn.execute("SELECT count(*) FROM schema_migrations WHERE version LIKE '%_down.sql'").fetchone()[0]
    contract = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='schema_migrations'").fetchone()[0]
    if bad:
        raise RuntimeError("rollback migration appears in schema_migrations")
    if not contract or tables < 39 or applied < len(_migration_files()):
        raise RuntimeError(f"PostgreSQL schema verification failed: tables={tables}, indexes={indexes}, constraints={constraints}, applied={applied}")
    print(f"POSTGRES_SCHEMA_VERIFIED tables={tables} indexes={indexes} constraints={constraints} migrations={applied} rollback_migrations={bad}", flush=True)


def _seed_configured_mcp_token(conn: psycopg.Connection[object]) -> None:
    token = os.environ.get("FABRIENT_MCP_AUTH_TOKEN", "").strip()
    secret = os.environ.get("AUTH_SECRET", "")
    if not token or len(secret) < 32:
        return
    token_hash = hmac.new(secret.encode(), token.encode(), hashlib.sha256).digest()
    web_origin = os.environ.get("FABRIENT_WEB_ORIGIN", "https://fabrient.com").rstrip("/")
    user = conn.execute("""INSERT INTO users(email, display_name, email_verified_at, role)
       VALUES('mcp-smoke@fabrient.local', 'MCP smoke service', now(), 'admin')
       ON CONFLICT ((lower(email))) DO UPDATE SET email_verified_at=coalesce(users.email_verified_at, now())
       RETURNING id""").fetchone()
    conn.execute("""INSERT INTO oauth_clients(client_id, client_name, redirect_uris, public_client)
       VALUES('fabrient-smoke', 'Fabrient MCP smoke service', %s, true)
       ON CONFLICT (client_id) DO NOTHING""", ([f"{web_origin}/oauth/callback"],))
    conn.execute("""INSERT INTO oauth_access_tokens(token_hash, client_id, user_id, scope, expires_at)
       VALUES(%s, 'fabrient-smoke', %s, 'openid email mcp:use', now() + interval '1 year')
       ON CONFLICT (token_hash) DO UPDATE SET revoked_at=null, expires_at=excluded.expires_at, scope=excluded.scope""", (token_hash, user[0]))


def _dsn() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL must be configured before MCP startup")
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def main() -> None:
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        conn.execute("select pg_advisory_lock(%s)", (MIGRATION_LOCK,))
        try:
            _apply_migrations(conn)
            _verify_schema(conn)
            _seed_configured_mcp_token(conn)
        finally:
            conn.execute("select pg_advisory_unlock(%s)", (MIGRATION_LOCK,))
    print("complete owned PostgreSQL schema migration applied", flush=True)


if __name__ == "__main__":
    main()

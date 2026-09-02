"""Apply the complete owned PostgreSQL schema before the MCP service starts.

This runner deliberately applies every forward migration on every startup. The
migrations are written to be idempotent, and this behavior is important for repair:
a previous broken deployment may have recorded migration markers while leaving the
actual schema incomplete. Rollback files are never executable at startup.
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
    files = sorted(
        p for p in _migration_dir().glob("*.sql") if not p.name.endswith("_down.sql")
    )
    if not files:
        raise RuntimeError("No PostgreSQL forward migrations found")
    return files


def _ensure_migration_table(conn: psycopg.Connection[object]) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )"""
    )


def _apply_migrations(conn: psycopg.Connection[object]) -> None:
    _ensure_migration_table(conn)
    for migration in _migration_files():
        print(f"applying PostgreSQL migration {migration.name}", flush=True)
        conn.execute(migration.read_text(encoding="utf-8"))


def _seed_configured_mcp_token(conn: psycopg.Connection[object]) -> None:
    token = os.environ.get("FABRIENT_MCP_AUTH_TOKEN", "").strip()
    secret = os.environ.get("AUTH_SECRET", "")
    if not token or len(secret) < 32:
        return
    token_hash = hmac.new(secret.encode(), token.encode(), hashlib.sha256).digest()
    user = conn.execute(
        """insert into users(email, display_name, email_verified_at, role)
           values('mcp-smoke@fabrient.local', 'MCP smoke service', now(), 'admin')
           on conflict ((lower(email))) do update set email_verified_at=coalesce(users.email_verified_at, now())
           returning id"""
    ).fetchone()
    conn.execute(
        """insert into oauth_clients(client_id, client_name, redirect_uris, public_client)
           values('fabrient-smoke', 'Fabrient MCP smoke service', ARRAY['https://fabrinat-omega.vercel.app/oauth/callback'], true)
           on conflict (client_id) do nothing"""
    )
    conn.execute(
        """insert into oauth_access_tokens(token_hash, client_id, user_id, scope, expires_at)
           values(%s, 'fabrient-smoke', %s, 'openid email mcp:use', now() + interval '1 year')
           on conflict (token_hash) do update set revoked_at=null, expires_at=excluded.expires_at, scope=excluded.scope""",
        (token_hash, user[0]),
    )


def _dsn() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL must be configured before MCP startup")
    if "sslmode=" not in url:
        url += ("&" if "?" in url else "?") + "sslmode=require"
    return url


def main() -> None:
    # A session-level advisory lock prevents Engineering and MCP from applying the
    # same repair migrations concurrently against the shared database.
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        conn.execute("select pg_advisory_lock(%s)", (MIGRATION_LOCK,))
        try:
            _apply_migrations(conn)
            _seed_configured_mcp_token(conn)
        finally:
            conn.execute("select pg_advisory_unlock(%s)", (MIGRATION_LOCK,))
    print("complete owned PostgreSQL schema migration applied", flush=True)


if __name__ == "__main__":
    main()

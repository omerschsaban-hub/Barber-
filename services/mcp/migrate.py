"""Apply the complete owned PostgreSQL schema before the MCP service starts.

The repository contains multiple additive migrations. The previous runner copied and
executed only two files, which meant production could boot with a partial schema.
This runner discovers every SQL migration shipped with the service, applies them in
stable filename order, and records a normalized filename marker after successful
application. All migrations are expected to be idempotent.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path

import psycopg


APP_MIGRATIONS = Path(__file__).with_name("migrations")
REPO_MIGRATIONS = Path(__file__).parents[2] / "db" / "migrations"


def _migration_dir() -> Path:
    """Return the migration directory available in the container or repository."""
    if APP_MIGRATIONS.is_dir():
        return APP_MIGRATIONS
    if REPO_MIGRATIONS.is_dir():
        return REPO_MIGRATIONS
    raise RuntimeError("PostgreSQL migration directory is missing")


def _migration_files() -> list[Path]:
    files = sorted(_migration_dir().glob("*.sql"), key=lambda p: p.name)
    if not files:
        raise RuntimeError("No PostgreSQL migrations found")
    return files


def _ensure_migration_table(conn: psycopg.Connection[object]) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )"""
    )


def _apply_migrations(conn: psycopg.Connection[object]) -> None:
    """Apply every repository migration exactly once by filename marker.

    Existing migrations also write their historical version markers. The filename
    marker is intentionally separate so migrations that predate the convention are
    still tracked reliably.
    """
    _ensure_migration_table(conn)
    for migration in _migration_files():
        marker = f"file:{migration.name}"
        already_applied = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE version = %s", (marker,)
        ).fetchone()
        if already_applied:
            continue
        conn.execute(migration.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO schema_migrations(version) VALUES (%s) ON CONFLICT DO NOTHING",
            (marker,),
        )


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
           on conflict (client_id) do nothing""",
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
    with psycopg.connect(_dsn()) as conn:
        with conn.transaction():
            _apply_migrations(conn)
            _seed_configured_mcp_token(conn)
    print("complete owned PostgreSQL schema migration applied", flush=True)


if __name__ == "__main__":
    main()

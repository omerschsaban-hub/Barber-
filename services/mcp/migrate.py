"""Apply the owned PostgreSQL schema before the MCP service starts.

The migration is idempotent and is intentionally run at container startup so
Render's free plan does not require an interactive shell or a separate job.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path

import psycopg


_LOCAL_MIGRATION = Path(__file__).with_name("001_owned_postgres.sql")
_REPO_MIGRATION = Path(__file__).parents[2] / "db" / "migrations" / "001_owned_postgres.sql"
MIGRATION = _LOCAL_MIGRATION if _LOCAL_MIGRATION.exists() else _REPO_MIGRATION


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
           values('fabrient-smoke', 'Fabrient MCP smoke service', ARRAY['https://fabrient.com/oauth/callback'], true)
           on conflict (client_id) do nothing"""
    )
    conn.execute(
        """insert into oauth_access_tokens(token_hash, client_id, user_id, scope, expires_at)
           values(%s, 'fabrient-smoke', %s, 'openid email mcp:use', now() + interval '1 year')
           on conflict (token_hash) do update set revoked_at=null, expires_at=excluded.expires_at, scope=excluded.scope""",
        (token_hash, user["id"]),
    )


def main() -> None:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL must be configured before MCP startup")
    sql = MIGRATION.read_text(encoding="utf-8")
    with psycopg.connect(url) as conn:
        with conn.transaction():
            conn.execute(sql)
            _seed_configured_mcp_token(conn)
    print("owned PostgreSQL schema migration applied", flush=True)


if __name__ == "__main__":
    main()

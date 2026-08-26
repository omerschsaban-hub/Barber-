from __future__ import annotations

import hashlib
import os
from typing import Any
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

_POOL: ConnectionPool | None = None

def _pool() -> ConnectionPool:
    global _POOL
    if _POOL is None:
        _POOL = ConnectionPool(os.environ["DATABASE_URL"], min_size=1, max_size=int(os.getenv("DB_POOL_MAX", "8")), kwargs={"row_factory": dict_row}, open=True)
    return _POOL

def _hash(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()

def user_from_bearer(token: str | None) -> dict[str, Any] | None:
    if not token: return None
    with _pool().connection() as conn:
        row = conn.execute("""select u.id::text as user_id,u.email,u.display_name
          from oauth_access_tokens t join users u on u.id=t.user_id
          where t.token_hash=%s and t.revoked_at is null and t.expires_at>now()""", (_hash(token),)).fetchone()
        if row: return dict(row)
        row = conn.execute("""select u.id::text as user_id,u.email,u.display_name
          from sessions s join users u on u.id=s.user_id
          where s.token_hash=%s and s.revoked_at is null and s.expires_at>now()""", (_hash(token),)).fetchone()
        return dict(row) if row else None

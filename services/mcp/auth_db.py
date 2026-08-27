from __future__ import annotations

import hashlib
import hmac
import os
import time
from collections import OrderedDict
from threading import Lock
from typing import Any

from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

_POOL: ConnectionPool | None = None
_AUTH_CACHE: OrderedDict[bytes, tuple[float, dict[str, Any] | None]] = OrderedDict()
_AUTH_CACHE_LOCK = Lock()
_AUTH_CACHE_TTL = max(0.0, min(float(os.getenv("AUTH_LOOKUP_CACHE_TTL", "5")), 30.0))
_AUTH_CACHE_MAX = max(100, min(int(os.getenv("AUTH_LOOKUP_CACHE_MAX", "10000")), 50000))


def _pool() -> ConnectionPool:
    global _POOL
    if _POOL is None:
        max_size = max(2, min(int(os.getenv("DB_POOL_MAX", "4")), 20))
        _POOL = ConnectionPool(
            os.environ["DATABASE_URL"],
            min_size=1,
            max_size=max_size,
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _POOL


def _hash(token: str) -> bytes:
    secret = os.environ.get("AUTH_SECRET")
    if not secret or len(secret) < 32:
        raise RuntimeError("AUTH_SECRET must be configured with at least 32 bytes of entropy")
    return hmac.new(secret.encode(), token.encode(), hashlib.sha256).digest()


def _cache_get(key: bytes) -> dict[str, Any] | None | object:
    if _AUTH_CACHE_TTL <= 0:
        return _MISS
    now = time.monotonic()
    with _AUTH_CACHE_LOCK:
        item = _AUTH_CACHE.get(key)
        if item is None:
            return _MISS
        expires, value = item
        if expires <= now:
            _AUTH_CACHE.pop(key, None)
            return _MISS
        _AUTH_CACHE.move_to_end(key)
        return dict(value) if value is not None else None


def _cache_put(key: bytes, value: dict[str, Any] | None) -> None:
    if _AUTH_CACHE_TTL <= 0:
        return
    with _AUTH_CACHE_LOCK:
        _AUTH_CACHE[key] = (time.monotonic() + _AUTH_CACHE_TTL, dict(value) if value is not None else None)
        _AUTH_CACHE.move_to_end(key)
        while len(_AUTH_CACHE) > _AUTH_CACHE_MAX:
            _AUTH_CACHE.popitem(last=False)


_MISS = object()


def user_from_bearer(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    token_hash = _hash(token)
    cached = _cache_get(token_hash)
    if cached is not _MISS:
        return cached

    with _pool().connection() as conn:
        row = conn.execute(
            """select u.id::text as user_id,u.email,u.display_name,t.scope, 'oauth' as auth_kind
              from oauth_access_tokens t join users u on u.id=t.user_id
              where t.token_hash=%s and t.revoked_at is null and t.expires_at>now()""",
            (token_hash,),
        ).fetchone()
        if row:
            result = dict(row)
            _cache_put(token_hash, result)
            return result
        row = conn.execute(
            """select u.id::text as user_id,u.email,u.display_name,'openid email' as scope, 'session' as auth_kind
              from sessions s join users u on u.id=s.user_id
              where s.token_hash=%s and s.revoked_at is null and s.expires_at>now()""",
            (token_hash,),
        ).fetchone()
        result = dict(row) if row else None
        _cache_put(token_hash, result)
        return result

from __future__ import annotations

import asyncio
import hashlib
import time
from collections import OrderedDict
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Only cache pure deterministic calculations. Never cache uploads, auth, billing,
# agents, manufacturing release, or any operation that can mutate state.
CACHEABLE_PATHS = frozenset({
    "/v1/predict",
    "/v1/simulate",
    "/v1/uncertainty",
    "/v1/acceptance",
    "/v1/reverification",
    "/v1/next-experiment",
})
CACHE_TTL = 60.0
CACHE_MAX = 512
_cache: OrderedDict[str, tuple[float, bytes, str, int]] = OrderedDict()
_lock = asyncio.Lock()


def _key(path: str, body: bytes) -> str:
    return hashlib.sha256(path.encode("utf-8") + b"\0" + body).hexdigest()


class DeterministicResponseCache(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Response:
        if request.method != "POST" or request.url.path not in CACHEABLE_PATHS:
            return await call_next(request)

        body = await request.body()
        key = _key(request.url.path, body)
        now = time.monotonic()
        async with _lock:
            item = _cache.get(key)
            if item and item[0] > now:
                _cache.move_to_end(key)
                return Response(item[1], status_code=item[3], media_type=item[2], headers={"X-Fabrient-Cache": "HIT", "Cache-Control": "private, max-age=60"})
            if item:
                _cache.pop(key, None)

        response = await call_next(request)
        if response.status_code != 200:
            return response

        content_type = response.headers.get("content-type", "application/json")
        if "application/json" not in content_type:
            return response

        chunks: list[bytes] = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        content = b"".join(chunks)
        async with _lock:
            _cache[key] = (time.monotonic() + CACHE_TTL, content, "application/json", response.status_code)
            _cache.move_to_end(key)
            while len(_cache) > CACHE_MAX:
                _cache.popitem(last=False)
        return Response(content, status_code=response.status_code, media_type="application/json", headers={"X-Fabrient-Cache": "MISS", "Cache-Control": "private, max-age=60"})

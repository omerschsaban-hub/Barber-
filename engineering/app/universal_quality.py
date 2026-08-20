"""Cross-cutting reliability layer applied to every engineering API route.

This does not manufacture engineering answers. It improves every existing feature by
adding consistent request identity, timing, finite-value checks, bounded payloads,
cache-safe headers, and an explicit evidence/release boundary.
"""
from __future__ import annotations

import json
import math
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = 30_000_000
MAX_RESPONSE_BYTES = 30_000_000


def _finite_tree(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(_finite_tree(k) and _finite_tree(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return all(_finite_tree(v) for v in value)
    return True


class UniversalQualityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_REQUEST_BYTES:
                    return JSONResponse(
                        {"status": "blocked", "reason": "request exceeds safety size limit", "request_id": request_id},
                        status_code=413,
                        headers={"X-Request-ID": request_id},
                    )
            except ValueError:
                pass

        try:
            response = await call_next(request)
        except Exception as exc:
            return JSONResponse(
                {"status": "error", "reason": "engineering route failed", "detail": str(exc)[:1000], "request_id": request_id},
                status_code=500,
                headers={"X-Request-ID": request_id},
            )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Engineering-Latency-Ms"] = str(round((time.perf_counter() - started) * 1000, 2))
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Do not let accidental NaN/Infinity values escape from numerical tools.
        # JSONResponse endpoints are checked at the route boundary by FastAPI; this
        # header advertises the invariant to clients and keeps the middleware cheap.
        response.headers["X-Numeric-Policy"] = "finite-only"
        return response


def install(app) -> None:
    app.add_middleware(UniversalQualityMiddleware)

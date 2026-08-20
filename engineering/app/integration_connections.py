from __future__ import annotations

"""User-authorized external engineering-system connections.

Credentials are never persisted here. Connection metadata lives in the caller's
session/configuration layer; secrets are supplied only at request time or via
server-side secret storage.
"""

import os
from typing import Any
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/integrations", tags=["integrations"])

PROVIDERS = {
    "autodesk_fusion": {
        "name": "Autodesk Fusion",
        "kind": "mcp",
        "docs": "https://help.autodesk.com/view/ADSKMCP/ENU/",
        "mode": "user-authorized MCP endpoint",
    },
    "propel_plm": {
        "name": "Propel PLM",
        "kind": "mcp",
        "docs": "https://www.propelsoftware.com/products/propel-mcp",
        "mode": "user-authorized MCP endpoint",
    },
}


class ConnectionTest(BaseModel):
    provider: str
    endpoint: str = Field(min_length=8)
    bearer_token: str | None = None


def _safe_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise HTTPException(status_code=400, detail="endpoint must be a valid HTTP(S) MCP endpoint")
    return endpoint


@router.get("/providers")
def list_providers() -> dict[str, Any]:
    return {"providers": [{"id": k, **v} for k, v in PROVIDERS.items()]}


@router.post("/test")
def test_connection(req: ConnectionTest) -> dict[str, Any]:
    provider = PROVIDERS.get(req.provider)
    if not provider:
        raise HTTPException(status_code=404, detail="unsupported provider")
    endpoint = _safe_endpoint(req.endpoint)
    headers = {"Accept": "application/json, text/event-stream"}
    if req.bearer_token:
        headers["Authorization"] = f"Bearer {req.bearer_token}"
    try:
        response = requests.get(endpoint, headers=headers, timeout=10)
        ok = response.status_code < 400
        return {
            "provider": req.provider,
            "connected": ok,
            "status_code": response.status_code,
            "endpoint": endpoint,
        }
    except requests.RequestException as exc:
        return {"provider": req.provider, "connected": False, "error": str(exc)}


@router.post("/mcp/configure")
def configure_connection(req: ConnectionTest) -> dict[str, Any]:
    """Validate a connection and return client-safe metadata.

    This endpoint intentionally does not persist bearer tokens. Production
    deployments should store secrets in the authenticated user's secret store.
    """
    result = test_connection(req)
    if not result.get("connected"):
        raise HTTPException(status_code=502, detail={"message": "external MCP connection failed", "result": result})
    return {
        "configured": True,
        "provider": req.provider,
        "endpoint": result["endpoint"],
        "credential_persisted": False,
    }

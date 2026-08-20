"""Provider-neutral gateway for authorized engineering-system integrations.

The gateway intentionally does not hard-code credentials or scrape third-party
systems. Providers are configured with environment variables and must expose an
approved MCP endpoint or API.  The first-class MCP targets are Autodesk Fusion
and Propel PLM; additional providers can be added without changing the product
workflow.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class ProviderConfig:
    key: str
    name: str
    transport: str
    endpoint_env: str
    token_env: str


PROVIDERS = {
    "autodesk_fusion": ProviderConfig(
        key="autodesk_fusion",
        name="Autodesk Fusion MCP",
        transport="mcp",
        endpoint_env="FABRIENT_FUSION_MCP_URL",
        token_env="FABRIENT_FUSION_MCP_TOKEN",
    ),
    "propel_plm": ProviderConfig(
        key="propel_plm",
        name="Propel PLM MCP",
        transport="mcp",
        endpoint_env="FABRIENT_PROPEL_MCP_URL",
        token_env="FABRIENT_PROPEL_MCP_TOKEN",
    ),
}


class IntegrationRequest(BaseModel):
    provider: str = Field(min_length=1)
    method: str = Field(default="tools/list", min_length=1)
    params: Dict[str, Any] = Field(default_factory=dict)


class MCPClient:
    """Minimal JSON-RPC MCP client for explicitly configured endpoints."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.endpoint = os.getenv(config.endpoint_env, "").strip()
        self.token = os.getenv(config.token_env, "").strip()

    @property
    def configured(self) -> bool:
        return bool(self.endpoint)

    async def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.endpoint:
            raise RuntimeError(f"{self.config.key} is not configured")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=False) as client:
            response = await client.post(self.endpoint, json=payload, headers=headers)
            response.raise_for_status()
            body = response.json()
        if not isinstance(body, dict):
            raise RuntimeError("MCP provider returned a non-object response")
        if "error" in body:
            raise RuntimeError(str(body["error"]))
        return body


def client_for(provider: str) -> MCPClient:
    config = PROVIDERS.get(provider)
    if not config:
        raise KeyError(provider)
    return MCPClient(config)


router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/providers")
async def providers() -> Dict[str, Any]:
    return {
        "providers": [
            {
                "key": config.key,
                "name": config.name,
                "transport": config.transport,
                "configured": client_for(config.key).configured,
            }
            for config in PROVIDERS.values()
        ]
    }


@router.post("/mcp/call")
async def mcp_call(request: IntegrationRequest) -> Dict[str, Any]:
    """Call an explicitly configured provider MCP endpoint.

    This endpoint is intentionally generic so the product can add providers
    without creating bespoke business logic for each vendor. Provider-side
    permissions remain authoritative.
    """
    try:
        client = client_for(request.provider)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown integration provider")
    try:
        return await client.call(request.method, request.params)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Provider HTTP error: {exc.response.status_code}")
    except (httpx.HTTPError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=str(exc))


async def inspect_provider(provider: str) -> Dict[str, Any]:
    client = client_for(provider)
    if not client.configured:
        return {"provider": provider, "configured": False, "tools": []}
    result = await client.call("tools/list", {})
    return {"provider": provider, "configured": True, "result": result}

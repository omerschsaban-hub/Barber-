from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

ENGINE_URL = os.getenv("FABRIENT_ENGINE_URL", "https://fabrient-engineering.onrender.com").rstrip("/")

mcp = MCPServer(
    "Fabrient Engineering",
    instructions="Deterministic engineering tools for the Fabrient physical-product workflow. Never invent measurements or engineering facts.",
)


@mcp.tool()
async def engine_health() -> dict[str, Any]:
    """Check whether the deployed Fabrient engineering API is reachable."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{ENGINE_URL}/health")
        return {"ok": response.is_success, "status_code": response.status_code, "engine_url": ENGINE_URL, "body": response.text[:2000]}
    except Exception as exc:
        return {"ok": False, "engine_url": ENGINE_URL, "error": str(exc)}


@mcp.tool()
def validate_dimension(nominal_mm: float, measured_mm: float, tolerance_mm: float) -> dict[str, Any]:
    """Deterministically classify one measured dimension against an explicit tolerance."""
    if tolerance_mm < 0:
        raise ValueError("tolerance_mm must be non-negative")
    deviation_mm = measured_mm - nominal_mm
    accepted = abs(deviation_mm) <= tolerance_mm
    return {
        "accepted": accepted,
        "nominal_mm": nominal_mm,
        "measured_mm": measured_mm,
        "tolerance_mm": tolerance_mm,
        "deviation_mm": deviation_mm,
        "decision_basis": "abs(measured_mm - nominal_mm) <= tolerance_mm",
    }


@mcp.tool()
def get_fabrient_capabilities() -> dict[str, Any]:
    """Return the MCP server's supported operations and engineering boundary."""
    return {
        "name": "Fabrient Engineering",
        "transport": "streamable-http",
        "tools": ["engine_health", "validate_dimension", "get_fabrient_capabilities"],
        "principles": [
            "deterministic calculations",
            "explicit provenance",
            "no invented measurements",
            "uncertainty must remain explicit",
        ],
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "fabrient-mcp"})


host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost")
security = TransportSecuritySettings(
    allowed_hosts=[host, f"{host}:*", "localhost", "localhost:*"],
    allowed_origins=[f"https://{host}", "http://localhost", "http://localhost:*"] if host != "localhost" else ["http://localhost", "http://localhost:*"] ,
)

app = mcp.streamable_http_app(transport_security=security)

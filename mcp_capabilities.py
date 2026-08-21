from __future__ import annotations

"""Compatibility capability registry for the legacy root MCP entrypoint.

The deployed MCP server's authoritative registry lives in services/mcp/server.py.
This module derives the two registries expected by the legacy FastMCP wrapper so
that the wrapper cannot silently fail because of a missing import or drift into a
second, hand-maintained tool list.
"""

from typing import Any

from services.mcp.server import CAPABILITY_REGISTRY

TOOLBOX_CAPABILITIES: dict[str, str] = {
    name: description
    for name, description, path in CAPABILITY_REGISTRY
    if path.startswith("/v1/toolbox/")
}

DIRECT_CAPABILITIES: dict[str, tuple[str, str]] = {
    name: (path, description)
    for name, description, path in CAPABILITY_REGISTRY
    if not path.startswith("/v1/toolbox/")
}

CAPABILITY_COUNT = len(TOOLBOX_CAPABILITIES) + len(DIRECT_CAPABILITIES)
if CAPABILITY_COUNT != len(CAPABILITY_REGISTRY):
    raise RuntimeError("Capability registry derivation lost entries")
if len({name for name, _, _ in CAPABILITY_REGISTRY}) != CAPABILITY_COUNT:
    raise RuntimeError("Capability registry contains duplicate names")

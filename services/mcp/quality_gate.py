from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from server import CAPABILITY_NAMES
from smoke_test import fixture

PLACEHOLDER_MARKERS = (
    'mcp_registry_compatibility_boundary',
    'provide operation-specific evidence',
    'reviewable',
    'unsupported_operation',
)


def rendered(result: Any) -> str:
    parts = []
    for block in getattr(result, 'content', []) or []:
        text = getattr(block, 'text', None)
        if text:
            parts.append(text)
    return ' '.join(parts)


def quality_failures(name: str, text: str) -> list[str]:
    low = text.lower()
    failures = []
    for marker in PLACEHOLDER_MARKERS:
        if marker in low:
            failures.append(f'{name}: placeholder/compatibility response contains {marker!r}')
    if not text.strip():
        failures.append(f'{name}: empty MCP content')
    try:
        obj = json.loads(text)
    except Exception:
        return failures
    if isinstance(obj, dict):
        provenance = obj.get('provenance')
        if provenance and provenance.get('synthetic') is True and name not in {'simulation_run', 'physics_predict'}:
            failures.append(f'{name}: synthetic provenance on a non-simulation tool')
        if obj.get('status') == 'generated' and not any(k in obj for k in ('artifact', 'content', 'files', 'package', 'document')):
            failures.append(f'{name}: generated status without a concrete artifact/content field')
    return failures


async def main() -> None:
    url = os.getenv('MCP_URL', 'http://127.0.0.1:8000/mcp')
    async with streamable_http_client(url) as streams:
        read_stream, write_stream = streams[:2]
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = [tool.name for tool in listed.tools]
            if names != CAPABILITY_NAMES:
                raise AssertionError(f'tools/list mismatch: expected {len(CAPABILITY_NAMES)}, got {len(names)}')
            failures: list[str] = []
            for name in CAPABILITY_NAMES:
                try:
                    args = fixture(name)
                    if name == 'validate_dimension':
                        result = await session.call_tool(name, arguments=args)
                    else:
                        result = await session.call_tool(name, arguments={'payload': args})
                    failures.extend(quality_failures(name, rendered(result)))
                except Exception as exc:
                    failures.append(f'{name}: exception: {exc}')
            if failures:
                raise AssertionError('Engineering quality gate failures:\n' + '\n'.join(failures))
            print(f'Engineering quality gate OK: tools/list={len(names)}, tools/call={len(names)}, failures=0')


if __name__ == '__main__':
    asyncio.run(main())

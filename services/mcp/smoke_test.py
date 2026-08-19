from __future__ import annotations

import asyncio
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from server import CAPABILITY_NAMES


async def main() -> None:
    url = os.getenv("MCP_URL", "http://127.0.0.1:8000/mcp")
    async with streamable_http_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed = await session.list_tools()
            names = [tool.name for tool in listed.tools]
            assert names == CAPABILITY_NAMES, "tools/list does not match the authoritative registry"
            assert len(names) == 100 and len(set(names)) == 100

            failures: list[str] = []
            for name in CAPABILITY_NAMES:
                try:
                    if name == "validate_dimension":
                        result = await session.call_tool(
                            name,
                            arguments={
                                "nominal_mm": 10.0,
                                "measured_mm": 10.0,
                                "tolerance_mm": 0.1,
                                "mcp_smoke_test": True,
                            },
                        )
                    else:
                        result = await session.call_tool(
                            name,
                            arguments={"payload": {"_mcp_smoke_test": True}},
                        )
                    if not result.content:
                        failures.append(f"{name}: empty result")
                except Exception as exc:
                    failures.append(f"{name}: {exc}")

            if failures:
                raise AssertionError("MCP tools/call failures:\n" + "\n".join(failures))
            print(f"MCP smoke OK: tools/list={len(names)}, tools/call={len(CAPABILITY_NAMES)}")


if __name__ == "__main__":
    asyncio.run(main())

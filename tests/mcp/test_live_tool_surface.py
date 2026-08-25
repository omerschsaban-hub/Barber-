"""Safe live surface test for the complete 100-tool MCP backing API.

This deliberately sends an empty, non-mutating request. The goal is to prove that every
registered operation resolves to a real backend route and returns a controlled response
(2xx or an expected client/auth/content error), rather than 404/405/5xx. Positive semantic
fixtures should be added per tool before a release is considered production-ready.
"""

import os
from pathlib import Path
import ast

import httpx
import pytest

SERVER = Path(__file__).parents[2] / "services" / "mcp" / "server.py"


def _registry():
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CAPABILITY_REGISTRY" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("CAPABILITY_REGISTRY not found")


@pytest.mark.live
@pytest.mark.parametrize("name,description,path", _registry(), ids=lambda row: row[0] if isinstance(row, tuple) else str(row))
def test_every_registered_tool_has_a_real_backend_surface(name, description, path):
    base = os.getenv("FABRIENT_ENGINE_URL")
    if not base:
        pytest.skip("Set FABRIENT_ENGINE_URL to run the live 100-tool surface test")

    url = f"{base.rstrip('/')}{path}"
    response = httpx.post(url, json={}, timeout=20.0)

    # 2xx means the route accepted the probe. 4xx means the route exists and
    # correctly rejected an intentionally incomplete/unauthorized probe.
    # 404/405 and all 5xx statuses are infrastructure/registration failures.
    assert response.status_code not in {404, 405}, f"{name} is not wired to {path}"
    assert response.status_code < 500, f"{name} returned server failure {response.status_code}: {response.text[:500]}"

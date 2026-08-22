"""Deterministic acceptance checks for the public Fabrient feature surface."""
from __future__ import annotations

import importlib
import json
import os
import urllib.request


def http_json(base: str, path: str, payload=None):
    url = base.rstrip('/') + path
    if payload is None:
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        assert 200 <= r.status < 300, (path, r.status)
        return json.loads(r.read() or b"{}")


def test_engineering_feature_surface():
    base = os.getenv("FABRIENT_ENGINE_URL", "http://127.0.0.1:8001")
    http_json(base, "/health")
    fixture = {
        "part_name": "Acceptance fixture",
        "revision": "A",
        "material": "PETG",
        "machine": "FDM printer",
        "measurements": {
            "wall_thickness_mm": 1.0,
            "clearance_mm": 0.15,
            "hole_diameter_mm": 2.4,
            "overhang_deg": 55,
            "bridge_mm": 8,
            "tolerance_mm": 0.2,
        },
    }
    analyze = http_json(base, "/v1/dfm/analyze", fixture)
    assert isinstance(analyze, dict)
    fixed = http_json(base, "/v1/dfm/self-fix", fixture)
    assert isinstance(fixed, dict)


def test_python_feature_modules_import():
    """Catch broken imports across the main deterministic feature modules."""
    modules = [
        "services.engine.main",
        "mcp_server",
        "mcp_capabilities",
    ]
    for module in modules:
        importlib.import_module(module)


def test_mcp_registry_is_complete():
    import mcp_server
    names = mcp_server.CAPABILITY_NAMES
    assert len(names) == 100
    assert len(set(names)) == 100
    assert all(name in mcp_server.CAPABILITIES for name in names)


if __name__ == "__main__":
    test_python_feature_modules_import()
    test_mcp_registry_is_complete()
    test_engineering_feature_surface()
    print("Fabrient feature acceptance checks passed")

from pathlib import Path

ROOT = Path(__file__).parents[2]
GATEWAY = ROOT / "services" / "mcp" / "runtime_gateway.py"
DOCKERFILE = ROOT / "services" / "mcp" / "Dockerfile"

CORE_TOOLS = {
    "inspect_part", "analyze_dfm", "verify_fixes", "validate_material", "validate_machine_envelope",
    "validate_dimension", "check_wall_thickness", "check_clearances", "check_holes", "check_overhangs",
    "check_orientation", "check_tolerances", "check_fit", "check_first_layer", "check_bed_adhesion",
}


def test_reliable_core_is_exactly_15_tools():
    source = GATEWAY.read_text(encoding="utf-8")
    assert source.count('"inspect_part"') == 1
    for tool in CORE_TOOLS:
        assert f'"{tool}"' in source
    assert source.count('"validate_dimension"') == 1


def test_gateway_uses_engine_as_auth_and_access_authority():
    source = GATEWAY.read_text(encoding="utf-8")
    assert '"/auth/me"' in source
    assert '"/v1/mcp/access"' in source
    assert '"MCP is transport/interface; Engineering API owns auth, billing, business logic, and Postgres"' in source


def test_gateway_forwards_bearer_to_engine_and_rate_limits():
    source = GATEWAY.read_text(encoding="utf-8")
    assert 'headers["Authorization"] = f"Bearer {token}"' in source
    assert '"rate_limited"' in source


def test_render_runs_gateway_and_checks_backend_readiness():
    source = DOCKERFILE.read_text(encoding="utf-8")
    assert "runtime_gateway:app" in source
    assert "auth_server:app" not in source


def test_live_catalog_is_not_the_full_100_tool_registry():
    source = GATEWAY.read_text(encoding="utf-8")
    assert 'getattr(mcp_server.mcp, "remove_tool", None)' in source
    assert "mcp_server.mcp._tool_manager._tools.pop(_tool.name, None)" in source
    assert "reliable_core_first" in source

import pytest

from app.integration_gateway import MCPClient
from app.mcp_integrations import MCP_PROVIDERS


def test_verified_providers_are_registered():
    expected = {
        "autodesk_product_help", "github", "linear", "cloudflare",
        "cloudflare_docs", "cloudflare_observability", "netlify", "notion", "vercel",
    }
    assert set(MCP_PROVIDERS) == expected
    assert all(config["kind"] == "official_remote" for config in MCP_PROVIDERS.values())
    assert all(config["endpoint"].startswith("https://") for config in MCP_PROVIDERS.values())


def test_clients_do_not_require_credentials_at_import_time(monkeypatch):
    for provider in MCP_PROVIDERS:
        monkeypatch.delenv(f"FABRIENT_{provider.upper()}_MCP_TOKEN", raising=False)
    assert MCPClient("autodesk_product_help").configured is True
    assert MCPClient("github").configured is False


def test_unknown_provider_is_rejected():
    with pytest.raises(KeyError):
        MCPClient("unknown_provider")

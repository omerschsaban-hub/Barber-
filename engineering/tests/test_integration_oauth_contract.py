from pathlib import Path

from app.integration_oauth import _pkce
from app.mcp_integrations import MCP_PROVIDERS

ROOT = Path(__file__).resolve().parents[2]


def test_oauth_connection_storage_contract_exists():
    sql = (ROOT / "db/migrations/011_integration_connections.sql").read_text()
    assert "CREATE TABLE IF NOT EXISTS integration_connections" in sql
    assert "CREATE TABLE IF NOT EXISTS integration_oauth_states" in sql
    assert "access_token_ciphertext" in sql
    assert "code_verifier_ciphertext" in sql


def test_pkce_uses_s256_shape():
    verifier, challenge = _pkce()
    assert len(verifier) >= 43
    assert challenge
    assert "=" not in challenge


def test_authenticated_catalog_providers_have_real_remote_endpoints():
    for provider, config in MCP_PROVIDERS.items():
        if config["auth"] != "public":
            assert config["endpoint"].startswith("https://")
            assert config["endpoint"].endswith("mcp") or config["endpoint"].endswith("mcp/")


def test_no_user_credentials_are_part_of_provider_catalog():
    for config in MCP_PROVIDERS.values():
        assert "client_secret" not in config
        assert "access_token" not in config
        assert "bearer_token" not in config

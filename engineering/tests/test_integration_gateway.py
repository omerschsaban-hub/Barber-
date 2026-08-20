import pytest

from app.integration_gateway import client_for, PROVIDERS


def test_verified_providers_are_registered():
    assert set(PROVIDERS) == {"autodesk_fusion", "propel_plm"}
    assert all(config.transport == "mcp" for config in PROVIDERS.values())


def test_clients_do_not_require_credentials_at_import_time(monkeypatch):
    monkeypatch.delenv("FABRIENT_FUSION_MCP_URL", raising=False)
    monkeypatch.delenv("FABRIENT_PROPEL_MCP_URL", raising=False)
    assert client_for("autodesk_fusion").configured is False
    assert client_for("propel_plm").configured is False


def test_unknown_provider_is_rejected():
    with pytest.raises(KeyError):
        client_for("unknown_provider")

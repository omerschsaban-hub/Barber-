import pytest

import app.storage as storage


def test_storage_is_unconfigured_without_all_required_values(monkeypatch):
    for key in ("STORAGE_BUCKET", "STORAGE_ENDPOINT", "STORAGE_ACCESS_KEY_ID", "STORAGE_SECRET_ACCESS_KEY"):
        monkeypatch.delenv(key, raising=False)
    assert storage.configured() is False


def test_production_requires_durable_storage(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    for key in ("STORAGE_BUCKET", "STORAGE_ENDPOINT", "STORAGE_ACCESS_KEY_ID", "STORAGE_SECRET_ACCESS_KEY"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(storage.StorageConfigurationError):
        storage.require_durable_storage()


def test_production_rejects_non_https_storage_endpoint(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("STORAGE_BUCKET", "fabrient")
    monkeypatch.setenv("STORAGE_ENDPOINT", "http://storage.internal")
    monkeypatch.setenv("STORAGE_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("STORAGE_SECRET_ACCESS_KEY", "secret")
    with pytest.raises(storage.StorageConfigurationError):
        storage._client()

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_schema_reconciliation_adds_legacy_missing_columns():
    sql = read("db/migrations/010_schema_reconciliation.sql")
    for fragment in ("ALTER TABLE public.users ADD COLUMN IF NOT EXISTS role", "ALTER TABLE public.oauth_clients ADD COLUMN IF NOT EXISTS client_name", "ALTER TABLE public.oauth_clients ADD COLUMN IF NOT EXISTS public_client", "ALTER TABLE public.billing_entitlements ADD COLUMN IF NOT EXISTS active", "ALTER TABLE public.billing_events ADD COLUMN IF NOT EXISTS occurred_at", "ALTER TABLE public.billing_events ADD COLUMN IF NOT EXISTS sequence_number"):
        assert fragment in sql


def test_artifact_schema_is_postgres_only():
    migration = read("db/migrations/011_postgres_artifacts.sql")
    store = read("engineering/app/postgres_artifacts.py")
    assert "CREATE TABLE IF NOT EXISTS artifact_metadata" in migration
    assert "CREATE TABLE IF NOT EXISTS artifact_data" in migration
    assert "BYTEA NOT NULL" in migration
    assert "from .postgres import get_conn" in store
    assert "S3" not in store and "boto3" not in store


def test_production_artifact_paths_use_postgres_and_never_object_storage():
    for rel in ("engineering/app/cad_routes.py", "engineering/app/cad_generation.py"):
        text = read(rel)
        assert "postgres_artifacts" in text
        assert "put_bytes" in text
        assert "download_url" not in text
        assert "object_storage" not in text
        assert "STORAGE_BUCKET" not in text
        assert "STORAGE_ACCESS_KEY_ID" not in text
        assert "STORAGE_SECRET_ACCESS_KEY" not in text


def test_artifact_download_is_authenticated_and_streamed():
    cad = read("engineering/app/cad_routes.py")
    store = read("engineering/app/postgres_artifacts.py")
    assert "_identity(request)" in cad
    assert "stream_bytes" in cad
    assert "substring(data FROM" in store


def test_auth_runtime_schema_matches_queries():
    auth = read("engineering/app/owned_auth.py")
    migration = read("db/migrations/001_owned_postgres.sql") + read("db/migrations/010_schema_reconciliation.sql")
    for column in ("users", "sessions", "otp_challenges", "role", "email_verified_at", "revoked_at"):
        assert column in migration
    for table in ("users", "sessions", "otp_challenges", "rate_limits", "audit_logs"):
        assert table in auth

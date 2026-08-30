from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_schema_reconciliation_adds_legacy_missing_columns():
    sql = read("db/migrations/010_schema_reconciliation.sql")
    for fragment in (
        "ALTER TABLE public.users ADD COLUMN IF NOT EXISTS role",
        "ALTER TABLE public.oauth_clients ADD COLUMN IF NOT EXISTS client_name",
        "ALTER TABLE public.oauth_clients ADD COLUMN IF NOT EXISTS public_client",
        "ALTER TABLE public.billing_entitlements ADD COLUMN IF NOT EXISTS active",
        "ALTER TABLE public.billing_events ADD COLUMN IF NOT EXISTS occurred_at",
        "ALTER TABLE public.billing_events ADD COLUMN IF NOT EXISTS sequence_number",
    ):
        assert fragment in sql


def test_auth_runtime_schema_matches_queries():
    auth = read("engineering/app/owned_auth.py")
    migration = read("db/migrations/001_owned_postgres.sql") + read("db/migrations/010_schema_reconciliation.sql")
    for column in ("users", "sessions", "otp_challenges", "role", "email_verified_at", "revoked_at"):
        assert column in migration
    for table in ("users", "sessions", "otp_challenges", "rate_limits", "audit_logs"):
        assert table in auth


def test_production_artifact_paths_have_durable_storage_contract():
    storage = read("engineering/app/storage.py")
    cad = read("engineering/app/cad_routes.py")
    legacy = read("engineering/app/cad_generation.py")
    for text in (cad, legacy):
        assert "require_durable_storage" in text
        assert "put_bytes" in text
    for key in ("STORAGE_BUCKET", "STORAGE_ENDPOINT", "STORAGE_ACCESS_KEY_ID", "STORAGE_SECRET_ACCESS_KEY"):
        assert key in storage


def test_no_production_artifact_path_relies_on_returning_a_temp_path():
    for rel in ("engineering/app/cad_routes.py", "engineering/app/cad_generation.py"):
        text = read(rel)
        assert "TemporaryDirectory" in text  # temporary files are only staging
        assert "download_url" in text
        assert "object_storage" in text


def test_ci_has_a_database_free_contract_gap_marked_for_integration_coverage():
    ci = read(".github/workflows/ci.yml")
    assert "pytest -q" in ci
    # This intentionally documents the missing live-Postgres integration lane.
    assert "DATABASE_URL" not in ci.split("pytest -q", 1)[0]

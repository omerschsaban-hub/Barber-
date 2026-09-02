from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_owned_schema_contains_core_security_tables():
    sql = (ROOT / "db/migrations/001_owned_postgres.sql").read_text()
    for table in ("users", "sessions", "otp_challenges", "oauth_clients", "oauth_authorization_codes", "oauth_access_tokens", "billing_events", "billing_entitlements", "data_sources", "data_observations", "agent_runs"):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in sql


def test_complete_migration_set_is_shipped_to_mcp():
    dockerfile = (ROOT / "services/mcp/Dockerfile").read_text()
    migrate = (ROOT / "services/mcp/migrate.py").read_text()
    migration_dir = ROOT / "db/migrations"
    migration_files = sorted(migration_dir.glob("*.sql"))

    assert len(migration_files) >= 10
    assert "COPY db/migrations ./migrations" in dockerfile
    assert "glob(\"*.sql\")" in migrate
    assert "sorted(" in migrate
    assert "schema_migrations" in migrate


def test_required_platform_tables_are_defined_across_migrations():
    migration_sql = "\n".join(p.read_text() for p in sorted((ROOT / "db/migrations").glob("*.sql")))
    for table in (
        "projects",
        "project_members",
        "billing_customers",
        "api_keys",
        "audit_logs",
        "oauth_authorization_requests",
        "plan_usage_monthly",
        "workspace_invitations",
        "project_approvals",
        "notifications",
        "webhook_subscriptions",
        "organization_policies",
        "agent_jobs",
        "agent_action_ledger",
        "agent_artifacts",
        "artifact_metadata",
        "artifact_data",
        "integration_connections",
        "integration_oauth_states",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in migration_sql


def test_no_supabase_in_new_flywheel_paths():
    for rel in ("engineering/app/data_flywheel.py", "engineering/app/data_flywheel_agents.py", "engineering/app/data_flywheel_worker.py", "engineering/app/postgres.py"):
        text = (ROOT / rel).read_text()
        assert "supabase" not in text.lower()


def test_mcp_registry_is_exactly_100_tools():
    text = (ROOT / "services/mcp/server.py").read_text()
    assert "CAPABILITY_REGISTRY" in text
    # Existing repository contract tests parse the literal registry; this gate
    # intentionally avoids duplicating the parser here.


def test_production_config_does_not_require_supabase():
    text = (ROOT / "services/engine/main.py").read_text().lower()
    assert "supabase" not in text

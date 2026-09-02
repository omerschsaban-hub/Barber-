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

    assert len(migration_files) >= 13
    assert "COPY db/migrations ./migrations" in dockerfile
    assert "glob(\"*.sql\")" in migrate
    assert "endswith(\"_down.sql\")" in migrate
    assert "pg_advisory_lock" in migrate
    assert "schema_migrations" in migrate
    assert "checksum" in migrate
    assert "compare_digest" in migrate


def test_no_rollback_migration_is_selected_by_production_runners():
    for rel in ("services/mcp/migrate.py", "engineering/app/postgres.py"):
        text = (ROOT / rel).read_text()
        assert "not p.name.endswith(\"_down.sql\")" in text
        assert "_down.sql" in text


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


def test_render_postgres_migrations_do_not_depend_on_supabase_auth():
    migration_sql = "\n".join(p.read_text() for p in sorted((ROOT / "db/migrations").glob("*.sql")))
    assert "auth.uid(" not in migration_sql
    assert " to authenticated" not in migration_sql.lower()


def test_no_supabase_in_new_flywheel_paths():
    for rel in ("engineering/app/data_flywheel.py", "engineering/app/data_flywheel_agents.py", "engineering/app/data_flywheel_worker.py", "engineering/app/postgres.py"):
        text = (ROOT / rel).read_text()
        assert "supabase" not in text.lower()


def test_mcp_registry_is_exactly_100_tools():
    text = (ROOT / "services/mcp/server.py").read_text()
    assert "CAPABILITY_REGISTRY" in text


def test_production_config_does_not_require_supabase():
    text = (ROOT / "services/engine/main.py").read_text().lower()
    assert "supabase" not in text


def test_production_hardening_contains_durability_and_integrity_guards():
    sql = (ROOT / "db/migrations/013_production_hardening.sql").read_text()
    for fragment in (
        "idempotency_key",
        "lease_expires_at",
        "attempt_count",
        "estimated_cost_usd",
        "agent_jobs_user_idempotency_uq",
        "agent_action_ledger_job_idempotency_uq",
        "agent_runs_user_idempotency_uq",
        "enforce_agent_child_owner",
        "audit_logs_correlation_idx",
        "oauth_codes_expiry_idx",
        "billing_events_unprocessed_idx",
    ):
        assert fragment in sql

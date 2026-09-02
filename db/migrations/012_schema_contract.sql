BEGIN;

-- Fail startup rather than allowing a partially-migrated production database to
-- appear healthy. This is intentionally a contract over the tables that the
-- current Engineering, MCP, billing, integrations, and agent runtimes require.
DO $$
DECLARE
  required_table TEXT;
  required_tables TEXT[] := ARRAY[
    'users',
    'sessions',
    'otp_challenges',
    'organizations',
    'organization_members',
    'projects',
    'project_members',
    'permissions',
    'role_permissions',
    'billing_customers',
    'billing_events',
    'billing_entitlements',
    'paypal_subscriptions',
    'oauth_clients',
    'oauth_authorization_codes',
    'oauth_access_tokens',
    'oauth_authorization_requests',
    'api_keys',
    'audit_logs',
    'plan_usage_monthly',
    'data_sources',
    'data_observations',
    'data_quality_checks',
    'agent_runs',
    'agent_checkpoints',
    'improvement_candidates',
    'flywheel_checkpoints',
    'rate_limits',
    'workspace_invitations',
    'project_approvals',
    'notifications',
    'webhook_subscriptions',
    'organization_policies',
    'agent_jobs',
    'agent_action_ledger',
    'agent_artifacts',
    'artifact_metadata',
    'artifact_data',
    'integration_connections',
    'integration_oauth_states'
  ];
BEGIN
  FOREACH required_table IN ARRAY required_tables LOOP
    IF NOT EXISTS (
      SELECT 1
      FROM information_schema.tables
      WHERE table_schema = 'public'
        AND table_name = required_table
        AND table_type = 'BASE TABLE'
    ) THEN
      RAISE EXCEPTION 'Fabrient PostgreSQL schema contract failed: missing public.%', required_table;
    END IF;
  END LOOP;
END $$;

DO $$
DECLARE
  required_column TEXT[];
BEGIN
  FOREACH required_column SLICE 1 IN ARRAY ARRAY[
    ARRAY['users','email'],
    ARRAY['users','role'],
    ARRAY['sessions','token_hash'],
    ARRAY['otp_challenges','code_hash'],
    ARRAY['projects','organization_id'],
    ARRAY['billing_entitlements','active'],
    ARRAY['billing_events','occurred_at'],
    ARRAY['oauth_clients','client_name'],
    ARRAY['oauth_clients','public_client'],
    ARRAY['oauth_authorization_codes','code_challenge'],
    ARRAY['data_observations','provenance'],
    ARRAY['agent_jobs','objective'],
    ARRAY['agent_action_ledger','decision_basis'],
    ARRAY['artifact_metadata','sha256'],
    ARRAY['integration_connections','access_token_ciphertext']
  ] LOOP
    IF NOT EXISTS (
      SELECT 1
      FROM information_schema.columns
      WHERE table_schema = 'public'
        AND table_name = required_column[1]
        AND column_name = required_column[2]
    ) THEN
      RAISE EXCEPTION 'Fabrient PostgreSQL schema contract failed: missing public.%.%', required_column[1], required_column[2];
    END IF;
  END LOOP;
END $$;

INSERT INTO schema_migrations(version)
VALUES ('012_schema_contract')
ON CONFLICT (version) DO NOTHING;
COMMIT;

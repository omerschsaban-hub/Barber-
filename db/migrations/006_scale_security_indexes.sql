BEGIN;

-- Query-shape indexes for high-read authentication, tenancy, flywheel and agent paths.
CREATE INDEX IF NOT EXISTS organization_members_user_idx ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS oauth_access_tokens_user_active_idx ON oauth_access_tokens(user_id, expires_at DESC) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS oauth_access_tokens_active_expiry_idx ON oauth_access_tokens(expires_at) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS oauth_authorization_codes_client_expiry_idx ON oauth_authorization_codes(client_id, expires_at DESC) WHERE consumed_at IS NULL;
CREATE INDEX IF NOT EXISTS billing_events_pending_idx ON billing_events(received_at DESC) WHERE processed_at IS NULL;
CREATE INDEX IF NOT EXISTS billing_entitlements_active_expiry_idx ON billing_entitlements(user_id, expires_at DESC) WHERE active = TRUE;
CREATE INDEX IF NOT EXISTS data_observations_project_time_idx ON data_observations(project_id, observed_at DESC) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS data_observations_source_event_time_idx ON data_observations(source_key, event_type, observed_at DESC);
CREATE INDEX IF NOT EXISTS data_quality_checks_observation_idx ON data_quality_checks(observation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS agent_runs_project_time_idx ON agent_runs(project_id, created_at DESC) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS improvement_candidates_project_status_idx ON improvement_candidates(project_id, status, updated_at DESC) WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS flywheel_checkpoints_candidate_time_idx ON flywheel_checkpoints(improvement_candidate_id, created_at DESC) WHERE improvement_candidate_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS audit_logs_org_time_idx ON audit_logs(organization_id, created_at DESC) WHERE organization_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS rate_limits_updated_idx ON rate_limits(updated_at);

INSERT INTO schema_migrations(version) VALUES ('006_scale_security_indexes') ON CONFLICT (version) DO NOTHING;
COMMIT;

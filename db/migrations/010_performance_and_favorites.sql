BEGIN;

-- User favorites are generic so the UI can favorite projects, records, engineering
-- results, or other stable product entities without duplicating tables per entity.
CREATE TABLE IF NOT EXISTS user_favorites (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  object_type TEXT NOT NULL CHECK (length(object_type) BETWEEN 1 AND 64),
  object_id TEXT NOT NULL CHECK (length(object_id) BETWEEN 1 AND 256),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, object_type, object_id)
);
CREATE INDEX IF NOT EXISTS user_favorites_recent_idx
  ON user_favorites(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS user_favorites_object_idx
  ON user_favorites(object_type, object_id);

-- High-frequency access paths used by auth, observations, and agent history.
CREATE INDEX IF NOT EXISTS oauth_access_tokens_active_user_idx
  ON oauth_access_tokens(user_id, expires_at DESC)
  WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS oauth_authorization_codes_active_client_idx
  ON oauth_authorization_codes(client_id, expires_at DESC)
  WHERE consumed_at IS NULL;
CREATE INDEX IF NOT EXISTS data_observations_project_recent_idx
  ON data_observations(project_id, observed_at DESC)
  WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS data_observations_validation_recent_idx
  ON data_observations(validation_state, observed_at DESC);
CREATE INDEX IF NOT EXISTS agent_runs_project_recent_idx
  ON agent_runs(project_id, created_at DESC)
  WHERE project_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS improvement_candidates_project_status_idx
  ON improvement_candidates(project_id, status, updated_at DESC)
  WHERE project_id IS NOT NULL;

INSERT INTO schema_migrations(version)
VALUES ('010_performance_and_favorites')
ON CONFLICT DO NOTHING;

COMMIT;

BEGIN;

-- Worker uses idempotent upserts for quality checks; make that conflict target real.
CREATE UNIQUE INDEX IF NOT EXISTS data_quality_checks_observation_check_uq
  ON data_quality_checks(observation_id, check_name);

-- Hot-path indexes for the continuous graph loop and recent audit reads.
CREATE INDEX IF NOT EXISTS data_observations_validation_recent_idx
  ON data_observations(validation_state, observed_at DESC);
CREATE INDEX IF NOT EXISTS data_observations_content_hash_idx
  ON data_observations(source_key, content_hash)
  WHERE content_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS agent_runs_run_id_idx
  ON agent_runs(run_id, created_at DESC);
CREATE INDEX IF NOT EXISTS agent_runs_agent_recent_idx
  ON agent_runs(agent_type, created_at DESC);
CREATE INDEX IF NOT EXISTS flywheel_checkpoints_recent_idx
  ON flywheel_checkpoints(created_at DESC);

COMMIT;

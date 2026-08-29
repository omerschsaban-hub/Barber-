BEGIN;

ALTER TABLE agent_runs ADD COLUMN IF NOT EXISTS run_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS data_quality_checks_observation_check_uq ON data_quality_checks(observation_id, check_name);
CREATE INDEX IF NOT EXISTS data_observations_validation_recent_idx ON data_observations(validation_state, observed_at DESC);
CREATE INDEX IF NOT EXISTS agent_runs_run_id_idx ON agent_runs(run_id, created_at DESC);
CREATE INDEX IF NOT EXISTS agent_runs_agent_recent_idx ON agent_runs(agent_type, created_at DESC);
CREATE INDEX IF NOT EXISTS flywheel_checkpoints_recent_idx ON flywheel_checkpoints(created_at DESC);

COMMIT;

BEGIN;

-- The worker rechecks a bounded recent window on every run. Make those checks idempotent
-- so repeated 30-minute passes do not create unbounded duplicate rows.
CREATE UNIQUE INDEX IF NOT EXISTS data_quality_checks_observation_name_uq ON data_quality_checks(observation_id, check_name);
CREATE INDEX IF NOT EXISTS data_observations_validation_recent_idx ON data_observations(validation_state, observed_at DESC);

INSERT INTO schema_migrations(version) VALUES ('007_flywheel_write_dedup') ON CONFLICT (version) DO NOTHING;
COMMIT;

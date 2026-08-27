BEGIN;

-- The worker rechecks a bounded recent window on every run. Remove legacy duplicates
-- first so the new uniqueness constraint is safe on an already-used database.
DELETE FROM data_quality_checks a
USING data_quality_checks b
WHERE a.observation_id = b.observation_id
  AND a.check_name = b.check_name
  AND a.created_at < b.created_at;

CREATE UNIQUE INDEX IF NOT EXISTS data_quality_checks_observation_name_uq ON data_quality_checks(observation_id, check_name);
CREATE INDEX IF NOT EXISTS data_observations_validation_recent_idx ON data_observations(validation_state, observed_at DESC);

INSERT INTO schema_migrations(version) VALUES ('007_flywheel_write_dedup') ON CONFLICT (version) DO NOTHING;
COMMIT;

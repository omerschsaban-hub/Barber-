BEGIN;

ALTER TABLE billing_events
  ADD COLUMN IF NOT EXISTS occurred_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS sequence_number BIGINT;

CREATE INDEX IF NOT EXISTS billing_events_app_user_time_idx
  ON billing_events(app_user_id, occurred_at DESC, received_at DESC);

INSERT INTO schema_migrations(version)
VALUES ('003_billing_event_order')
ON CONFLICT DO NOTHING;

COMMIT;

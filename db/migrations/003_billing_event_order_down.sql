BEGIN;

DROP INDEX IF EXISTS billing_events_app_user_time_idx;
ALTER TABLE billing_events
  DROP COLUMN IF EXISTS sequence_number,
  DROP COLUMN IF EXISTS occurred_at;
DELETE FROM schema_migrations WHERE version = '003_billing_event_order';

COMMIT;

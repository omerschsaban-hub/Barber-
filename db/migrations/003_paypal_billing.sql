BEGIN;

CREATE TABLE IF NOT EXISTS paypal_subscriptions (
  paypal_subscription_id TEXT PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan TEXT NOT NULL CHECK (plan IN ('hobbyist','startup')),
  product_id TEXT NOT NULL,
  entitlement_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('APPROVAL_PENDING','ACTIVE','SUSPENDED','INACTIVE')),
  environment TEXT NOT NULL CHECK (environment IN ('sandbox','production')),
  request_id TEXT NOT NULL UNIQUE,
  last_event_id TEXT,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS paypal_subscriptions_user_idx ON paypal_subscriptions(user_id, updated_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS paypal_one_open_subscription_per_user_idx
  ON paypal_subscriptions(user_id)
  WHERE status IN ('APPROVAL_PENDING','ACTIVE','SUSPENDED');
CREATE INDEX IF NOT EXISTS paypal_subscriptions_event_idx ON paypal_subscriptions(last_event_id);

INSERT INTO schema_migrations(version) VALUES('003_paypal_billing') ON CONFLICT DO NOTHING;
COMMIT;

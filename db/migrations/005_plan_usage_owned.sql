CREATE TABLE IF NOT EXISTS plan_usage_monthly (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  period_start DATE NOT NULL,
  llm_runs INTEGER NOT NULL DEFAULT 0 CHECK (llm_runs >= 0),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, period_start)
);
CREATE INDEX IF NOT EXISTS plan_usage_period_idx ON plan_usage_monthly(period_start);

INSERT INTO schema_migrations(version) VALUES ('005_plan_usage_owned')
ON CONFLICT (version) DO NOTHING;

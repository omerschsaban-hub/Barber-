CREATE TABLE IF NOT EXISTS integration_oauth_transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    state_hash BYTEA NOT NULL UNIQUE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    return_path TEXT NOT NULL DEFAULT '/integrations',
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_integration_oauth_transactions_user_provider
    ON integration_oauth_transactions(user_id, provider, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_integration_oauth_transactions_expiry
    ON integration_oauth_transactions(expires_at);

BEGIN;

CREATE TABLE IF NOT EXISTS integration_connections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  provider_account_id TEXT,
  access_token_ciphertext BYTEA NOT NULL,
  refresh_token_ciphertext BYTEA,
  token_type TEXT NOT NULL DEFAULT 'Bearer',
  scopes TEXT[] NOT NULL DEFAULT '{}',
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, provider)
);
CREATE INDEX IF NOT EXISTS integration_connections_user_idx ON integration_connections(user_id);

CREATE TABLE IF NOT EXISTS integration_oauth_states (
  state_hash BYTEA PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  provider TEXT NOT NULL,
  code_verifier_ciphertext BYTEA NOT NULL,
  redirect_uri TEXT NOT NULL,
  client_id TEXT,
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS integration_oauth_states_expiry_idx ON integration_oauth_states(expires_at);

COMMIT;

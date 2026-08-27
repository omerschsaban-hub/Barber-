BEGIN;
CREATE TABLE IF NOT EXISTS oauth_authorization_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id TEXT NOT NULL REFERENCES oauth_clients(client_id) ON DELETE CASCADE,
  redirect_uri TEXT NOT NULL,
  scope TEXT NOT NULL DEFAULT 'openid email',
  state TEXT,
  code_challenge TEXT,
  code_challenge_method TEXT,
  expires_at TIMESTAMPTZ NOT NULL,
  approved_at TIMESTAMPTZ,
  denied_at TIMESTAMPTZ,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS oauth_requests_expiry_idx ON oauth_authorization_requests(expires_at);
CREATE INDEX IF NOT EXISTS oauth_requests_user_idx ON oauth_authorization_requests(user_id);
INSERT INTO schema_migrations(version) VALUES('004_owned_oauth_requests') ON CONFLICT DO NOTHING;
COMMIT;

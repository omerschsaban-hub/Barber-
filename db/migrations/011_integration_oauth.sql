BEGIN;

-- OAuth transactions used by engineering/app/integration_oauth.py.
CREATE TABLE IF NOT EXISTS public.integration_oauth_states (
    state_hash BYTEA PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    code_verifier_ciphertext BYTEA NOT NULL,
    redirect_uri TEXT NOT NULL,
    client_id TEXT,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS integration_oauth_states_expiry_idx
    ON public.integration_oauth_states(expires_at);

CREATE INDEX IF NOT EXISTS integration_oauth_states_user_provider_idx
    ON public.integration_oauth_states(user_id, provider, created_at DESC);

CREATE TABLE IF NOT EXISTS public.integration_connections (
    user_id BIGINT NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    access_token_ciphertext BYTEA NOT NULL,
    refresh_token_ciphertext BYTEA,
    token_type TEXT NOT NULL DEFAULT 'Bearer',
    scopes TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, provider)
);

CREATE INDEX IF NOT EXISTS integration_connections_provider_idx
    ON public.integration_connections(provider);

COMMIT;

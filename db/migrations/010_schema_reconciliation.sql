BEGIN;

-- 0001_platform_auth.sql predates the owned schema and CREATE TABLE IF NOT EXISTS
-- cannot add columns to an already-existing table. Reconcile those deployments
-- explicitly so the current application contract is present.
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS role TEXT;
UPDATE public.users SET role = 'member' WHERE role IS NULL;
ALTER TABLE public.users ALTER COLUMN role SET DEFAULT 'member';
ALTER TABLE public.users ALTER COLUMN role SET NOT NULL;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'users_role_check') THEN
    ALTER TABLE public.users ADD CONSTRAINT users_role_check CHECK (role IN ('member','admin'));
  END IF;
END $$;

ALTER TABLE public.oauth_clients ADD COLUMN IF NOT EXISTS client_name TEXT;
UPDATE public.oauth_clients SET client_name = client_id WHERE client_name IS NULL;
ALTER TABLE public.oauth_clients ALTER COLUMN client_name SET DEFAULT '';
ALTER TABLE public.oauth_clients ALTER COLUMN client_name SET NOT NULL;
ALTER TABLE public.oauth_clients ADD COLUMN IF NOT EXISTS public_client BOOLEAN;
UPDATE public.oauth_clients SET public_client = (client_secret_hash IS NULL) WHERE public_client IS NULL;
ALTER TABLE public.oauth_clients ALTER COLUMN public_client SET DEFAULT TRUE;
ALTER TABLE public.oauth_clients ALTER COLUMN public_client SET NOT NULL;

ALTER TABLE public.billing_entitlements ADD COLUMN IF NOT EXISTS active BOOLEAN;
UPDATE public.billing_entitlements SET active = (status = 'active') WHERE active IS NULL;
ALTER TABLE public.billing_entitlements ALTER COLUMN active SET DEFAULT FALSE;
ALTER TABLE public.billing_entitlements ALTER COLUMN active SET NOT NULL;
ALTER TABLE public.billing_entitlements ADD COLUMN IF NOT EXISTS source TEXT;
UPDATE public.billing_entitlements SET source = 'legacy' WHERE source IS NULL;
ALTER TABLE public.billing_entitlements ALTER COLUMN source SET DEFAULT 'legacy';
ALTER TABLE public.billing_entitlements ALTER COLUMN source SET NOT NULL;

-- Current billing code expects the event ordering columns introduced later.
ALTER TABLE public.billing_events ADD COLUMN IF NOT EXISTS occurred_at TIMESTAMPTZ;
ALTER TABLE public.billing_events ADD COLUMN IF NOT EXISTS sequence_number BIGINT;

CREATE INDEX IF NOT EXISTS users_role_idx ON public.users(role);
CREATE INDEX IF NOT EXISTS oauth_access_tokens_active_idx ON public.oauth_access_tokens(expires_at) WHERE revoked_at IS NULL;

INSERT INTO schema_migrations(version) VALUES ('010_schema_reconciliation') ON CONFLICT DO NOTHING;
COMMIT;

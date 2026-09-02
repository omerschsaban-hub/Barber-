BEGIN;

-- Production hardening is additive and intentionally avoids destructive cleanup.
-- Existing rows are preserved; NOT VALID checks protect all new writes while
-- allowing legacy data to be audited separately.

ALTER TABLE public.agent_jobs
  ADD COLUMN IF NOT EXISTS request_id TEXT,
  ADD COLUMN IF NOT EXISTS idempotency_key TEXT,
  ADD COLUMN IF NOT EXISTS parent_job_id UUID,
  ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS last_error TEXT,
  ADD COLUMN IF NOT EXISTS lease_expires_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

ALTER TABLE public.agent_runs
  ADD COLUMN IF NOT EXISTS request_id TEXT,
  ADD COLUMN IF NOT EXISTS idempotency_key TEXT,
  ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS input_tokens BIGINT,
  ADD COLUMN IF NOT EXISTS output_tokens BIGINT,
  ADD COLUMN IF NOT EXISTS total_tokens BIGINT,
  ADD COLUMN IF NOT EXISTS estimated_cost_usd NUMERIC(14,8);

ALTER TABLE public.agent_action_ledger
  ADD COLUMN IF NOT EXISTS idempotency_key TEXT;

ALTER TABLE public.agent_artifacts
  ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS immutable BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE public.audit_logs
  ADD COLUMN IF NOT EXISTS actor_type TEXT NOT NULL DEFAULT 'user',
  ADD COLUMN IF NOT EXISTS correlation_id TEXT,
  ADD COLUMN IF NOT EXISTS severity TEXT NOT NULL DEFAULT 'info';

ALTER TABLE public.audit_logs
  ADD CONSTRAINT audit_logs_actor_type_ck
  CHECK (actor_type IN ('user','agent','system')) NOT VALID;
ALTER TABLE public.audit_logs
  ADD CONSTRAINT audit_logs_severity_ck
  CHECK (severity IN ('debug','info','warning','error','critical')) NOT VALID;

ALTER TABLE public.agent_jobs
  ADD CONSTRAINT agent_jobs_attempt_count_ck
  CHECK (attempt_count >= 0) NOT VALID;

ALTER TABLE public.agent_runs
  ADD CONSTRAINT agent_runs_attempt_count_ck
  CHECK (attempt_count >= 0) NOT VALID;

ALTER TABLE public.agent_runs
  ADD CONSTRAINT agent_runs_token_counts_ck
  CHECK (
    (input_tokens IS NULL OR input_tokens >= 0) AND
    (output_tokens IS NULL OR output_tokens >= 0) AND
    (total_tokens IS NULL OR total_tokens >= 0) AND
    (estimated_cost_usd IS NULL OR estimated_cost_usd >= 0)
  ) NOT VALID;

ALTER TABLE public.oauth_authorization_codes
  ADD CONSTRAINT oauth_codes_pkce_method_ck
  CHECK (code_challenge_method IS NULL OR code_challenge_method = 'S256') NOT VALID;

-- Idempotency and hot-path indexes.
CREATE UNIQUE INDEX IF NOT EXISTS agent_jobs_user_idempotency_uq
  ON public.agent_jobs(user_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS agent_jobs_status_lease_idx
  ON public.agent_jobs(status, lease_expires_at)
  WHERE status IN ('active','blocked','ready');
CREATE INDEX IF NOT EXISTS agent_jobs_next_action_idx
  ON public.agent_jobs(next_action, updated_at DESC);
CREATE INDEX IF NOT EXISTS agent_jobs_parent_idx
  ON public.agent_jobs(parent_job_id)
  WHERE parent_job_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS agent_action_ledger_job_idempotency_uq
  ON public.agent_action_ledger(job_id, idempotency_key)
  WHERE idempotency_key IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS agent_runs_user_idempotency_uq
  ON public.agent_runs(project_id, idempotency_key)
  WHERE project_id IS NOT NULL AND idempotency_key IS NOT NULL;
CREATE INDEX IF NOT EXISTS agent_runs_project_status_idx
  ON public.agent_runs(project_id, status, created_at DESC);
CREATE INDEX IF NOT EXISTS audit_logs_org_time_idx
  ON public.audit_logs(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS audit_logs_correlation_idx
  ON public.audit_logs(correlation_id)
  WHERE correlation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS oauth_codes_expiry_idx
  ON public.oauth_authorization_codes(expires_at)
  WHERE consumed_at IS NULL;
CREATE INDEX IF NOT EXISTS oauth_tokens_user_active_idx
  ON public.oauth_access_tokens(user_id, expires_at)
  WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS sessions_user_active_idx
  ON public.sessions(user_id, expires_at)
  WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS otp_active_idx
  ON public.otp_challenges(lower(email), expires_at)
  WHERE consumed_at IS NULL;
CREATE INDEX IF NOT EXISTS billing_events_unprocessed_idx
  ON public.billing_events(received_at)
  WHERE processed_at IS NULL;
CREATE INDEX IF NOT EXISTS webhook_idempotency_recent_idx
  ON public.webhook_idempotency(received_at DESC);
CREATE INDEX IF NOT EXISTS integration_oauth_states_active_idx
  ON public.integration_oauth_states(expires_at)
  WHERE consumed_at IS NULL;
CREATE INDEX IF NOT EXISTS workspace_invitations_active_idx
  ON public.workspace_invitations(organization_id, expires_at)
  WHERE accepted_at IS NULL;
CREATE INDEX IF NOT EXISTS notifications_unread_idx
  ON public.notifications(user_id, created_at DESC)
  WHERE read_at IS NULL;

-- Parent/child ownership invariants for agent records. These are database-level
-- guardrails in addition to application authorization.
CREATE OR REPLACE FUNCTION public.enforce_agent_child_owner()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER AS $$
DECLARE
  owner_id UUID;
BEGIN
  SELECT user_id INTO owner_id FROM public.agent_jobs WHERE id = NEW.job_id;
  IF owner_id IS NULL THEN
    RAISE EXCEPTION 'agent job % does not exist', NEW.job_id;
  END IF;
  IF NEW.user_id <> owner_id THEN
    RAISE EXCEPTION 'agent child owner mismatch for job %', NEW.job_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS agent_action_owner_guard ON public.agent_action_ledger;
CREATE TRIGGER agent_action_owner_guard
BEFORE INSERT OR UPDATE OF job_id, user_id ON public.agent_action_ledger
FOR EACH ROW EXECUTE FUNCTION public.enforce_agent_child_owner();

DROP TRIGGER IF EXISTS agent_artifact_owner_guard ON public.agent_artifacts;
CREATE TRIGGER agent_artifact_owner_guard
BEFORE INSERT OR UPDATE OF job_id, user_id ON public.agent_artifacts
FOR EACH ROW EXECUTE FUNCTION public.enforce_agent_child_owner();

-- Keep all mutable updated_at columns consistent without requiring every caller
-- to remember to set them manually.
CREATE OR REPLACE FUNCTION public.touch_updated_at()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS users_touch_updated_at ON public.users;
CREATE TRIGGER users_touch_updated_at BEFORE UPDATE ON public.users
FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();
DROP TRIGGER IF EXISTS projects_touch_updated_at ON public.projects;
CREATE TRIGGER projects_touch_updated_at BEFORE UPDATE ON public.projects
FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();
DROP TRIGGER IF EXISTS billing_customers_touch_updated_at ON public.billing_customers;
CREATE TRIGGER billing_customers_touch_updated_at BEFORE UPDATE ON public.billing_customers
FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();
DROP TRIGGER IF EXISTS billing_entitlements_touch_updated_at ON public.billing_entitlements;
CREATE TRIGGER billing_entitlements_touch_updated_at BEFORE UPDATE ON public.billing_entitlements
FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();
DROP TRIGGER IF EXISTS integration_connections_touch_updated_at ON public.integration_connections;
CREATE TRIGGER integration_connections_touch_updated_at BEFORE UPDATE ON public.integration_connections
FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();
DROP TRIGGER IF EXISTS improvement_candidates_touch_updated_at ON public.improvement_candidates;
CREATE TRIGGER improvement_candidates_touch_updated_at BEFORE UPDATE ON public.improvement_candidates
FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();
DROP TRIGGER IF EXISTS organization_policies_touch_updated_at ON public.organization_policies;
CREATE TRIGGER organization_policies_touch_updated_at BEFORE UPDATE ON public.organization_policies
FOR EACH ROW EXECUTE FUNCTION public.touch_updated_at();

INSERT INTO schema_migrations(version) VALUES ('013_production_hardening') ON CONFLICT DO NOTHING;
COMMIT;

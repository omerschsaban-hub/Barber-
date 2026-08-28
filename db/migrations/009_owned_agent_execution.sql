create extension if not exists pgcrypto;

create table if not exists public.agent_jobs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  project_id uuid null,
  objective text not null,
  constraints jsonb not null default '{}'::jsonb,
  inputs jsonb not null default '{}'::jsonb,
  evidence_requirements jsonb not null default '[]'::jsonb,
  allowed_actions jsonb not null default '[]'::jsonb,
  approvals jsonb not null default '{}'::jsonb,
  state text not null default 'defined' check (state in ('defined','analyzing','blocked','ready','building','verifying','released')),
  status text not null default 'active' check (status in ('active','blocked','ready','released')),
  next_action text not null default 'inspect_job',
  blocker jsonb null,
  completion_criteria jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists agent_jobs_user_updated_idx on public.agent_jobs(user_id, updated_at desc);
create index if not exists agent_jobs_project_idx on public.agent_jobs(project_id);

create table if not exists public.agent_action_ledger (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references public.agent_jobs(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  actor_type text not null check (actor_type in ('human','agent','system')),
  action text not null,
  status text not null check (status in ('accepted','blocked','completed','failed')),
  inputs jsonb not null default '{}'::jsonb,
  outputs jsonb not null default '{}'::jsonb,
  evidence jsonb not null default '[]'::jsonb,
  decision_basis text,
  request_id text,
  created_at timestamptz not null default now()
);

create index if not exists agent_action_ledger_job_created_idx on public.agent_action_ledger(job_id, created_at desc);
create index if not exists agent_action_ledger_user_created_idx on public.agent_action_ledger(user_id, created_at desc);

create table if not exists public.agent_artifacts (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references public.agent_jobs(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  artifact_type text not null,
  name text not null,
  uri text,
  sha256 text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists agent_artifacts_job_created_idx on public.agent_artifacts(job_id, created_at desc);

create or replace function public.touch_agent_job()
returns trigger language plpgsql security invoker as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists agent_job_touch on public.agent_jobs;
create trigger agent_job_touch before update on public.agent_jobs for each row execute function public.touch_agent_job();

alter table public.agent_jobs enable row level security;
alter table public.agent_action_ledger enable row level security;
alter table public.agent_artifacts enable row level security;

grant select, insert, update, delete on public.agent_jobs to authenticated;
grant select, insert on public.agent_action_ledger to authenticated;
grant select, insert on public.agent_artifacts to authenticated;

 drop policy if exists "agent jobs own" on public.agent_jobs;
create policy "agent jobs own" on public.agent_jobs for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "agent ledger own" on public.agent_action_ledger;
create policy "agent ledger own" on public.agent_action_ledger for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "agent artifacts own" on public.agent_artifacts;
create policy "agent artifacts own" on public.agent_artifacts for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

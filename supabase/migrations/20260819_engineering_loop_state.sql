create table if not exists public.engineering_loop_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  project_id uuid null,
  stage text not null default 'analyze' check (stage in ('analyze','review','build','inspect','reverify','released')),
  next_action text not null default 'Run your first deterministic check.',
  status text not null default 'active' check (status in ('active','blocked','ready','released')),
  unresolved_issues jsonb not null default '[]'::jsonb,
  evidence_summary jsonb not null default '{}'::jsonb,
  last_action text,
  last_activity_at timestamptz not null default now(),
  share_token text unique,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists engineering_loop_state_activity_idx on public.engineering_loop_state(last_activity_at desc);
create index if not exists engineering_loop_state_project_idx on public.engineering_loop_state(project_id);

alter table public.engineering_loop_state enable row level security;
grant select, insert, update, delete on public.engineering_loop_state to authenticated;
revoke all on public.engineering_loop_state from anon;

drop policy if exists "users can read own engineering loop" on public.engineering_loop_state;
drop policy if exists "users can insert own engineering loop" on public.engineering_loop_state;
drop policy if exists "users can update own engineering loop" on public.engineering_loop_state;
drop policy if exists "users can delete own engineering loop" on public.engineering_loop_state;
create policy "users can read own engineering loop" on public.engineering_loop_state for select to authenticated using ((select auth.uid()) = user_id);
create policy "users can insert own engineering loop" on public.engineering_loop_state for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "users can update own engineering loop" on public.engineering_loop_state for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users can delete own engineering loop" on public.engineering_loop_state for delete to authenticated using ((select auth.uid()) = user_id);

create or replace function public.touch_engineering_loop_state()
returns trigger language plpgsql security invoker as $$
begin
  new.updated_at = now();
  new.last_activity_at = now();
  return new;
end;
$$;

drop trigger if exists engineering_loop_state_touch on public.engineering_loop_state;
create trigger engineering_loop_state_touch before update on public.engineering_loop_state for each row execute function public.touch_engineering_loop_state();

create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  email_verified_at timestamptz,
  display_name text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists otp_challenges (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  code_hash bytea not null,
  expires_at timestamptz not null,
  attempts integer not null default 0 check (attempts >= 0 and attempts <= 10),
  consumed_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists otp_challenges_email_created_idx on otp_challenges(email, created_at desc);

create table if not exists sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  token_hash bytea not null unique,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  created_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now()
);
create index if not exists sessions_user_idx on sessions(user_id, expires_at desc);
create index if not exists sessions_active_idx on sessions(token_hash) where revoked_at is null;

create table if not exists billing_entitlements (
  user_id uuid not null references users(id) on delete cascade,
  entitlement_id text not null,
  product_id text,
  status text not null default 'active',
  expires_at timestamptz,
  source_event_id text,
  updated_at timestamptz not null default now(),
  primary key (user_id, entitlement_id)
);

create table if not exists oauth_clients (
  client_id text primary key,
  client_secret_hash bytea,
  redirect_uris text[] not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists oauth_codes (
  code_hash bytea primary key,
  client_id text not null references oauth_clients(client_id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  redirect_uri text not null,
  code_challenge text,
  code_challenge_method text,
  scope text not null default 'openid email profile',
  expires_at timestamptz not null,
  consumed_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists auth_rate_limits (
  bucket_key text primary key,
  window_started_at timestamptz not null,
  attempts integer not null default 0
);

create or replace function touch_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end; $$;
drop trigger if exists users_touch_updated_at on users;
create trigger users_touch_updated_at before update on users for each row execute function touch_updated_at();

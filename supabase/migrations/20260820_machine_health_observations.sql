create table if not exists public.machine_health_observations (
  id uuid primary key default gen_random_uuid(), machine_id text not null, observed_at timestamptz not null,
  dimensional_deviation_mm double precision, correction_mm double precision, correction_direction double precision,
  ambient_temperature_c double precision, ambient_rh_pct double precision, dew_point_c double precision, atmospheric_pressure_kpa double precision,
  filament_temperature_c double precision, filament_rh_pct double precision, filament_lot text, nozzle_hours double precision,
  pressure_advance double precision, resonance_x_hz double precision, resonance_y_hz double precision, vibration_amplitude double precision,
  shaper_x text, shaper_y text, frequency_spectrum jsonb, reference_artifact boolean not null default false,
  source text not null default 'user_observation', provenance jsonb not null default '{}'::jsonb, created_at timestamptz not null default now()
);
create index if not exists machine_health_observations_machine_time_idx on public.machine_health_observations(machine_id,observed_at desc);
alter table public.machine_health_observations enable row level security;
drop policy if exists "users can read machine health" on public.machine_health_observations;
create policy "users can read machine health" on public.machine_health_observations for select to authenticated using (true);
drop policy if exists "users can insert machine health" on public.machine_health_observations;
create policy "users can insert machine health" on public.machine_health_observations for insert to authenticated with check (true);

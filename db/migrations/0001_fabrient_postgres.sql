BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Tenancy / enterprise foundation. User identity remains externally owned during the first cutover.
CREATE TABLE IF NOT EXISTS organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text NOT NULL UNIQUE,
  plan text NOT NULL DEFAULT 'individual',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS organization_members (
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id uuid NOT NULL,
  role text NOT NULL DEFAULT 'member',
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, user_id)
);

CREATE TABLE IF NOT EXISTS projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  description text,
  organization_id uuid REFERENCES organizations(id) ON DELETE CASCADE,
  owner_id uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS project_members (
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id uuid NOT NULL,
  role text NOT NULL DEFAULT 'member',
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (project_id, user_id)
);

CREATE TABLE IF NOT EXISTS machines (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name text NOT NULL, manufacturer text, model text, process text NOT NULL DEFAULT 'FDM', metadata jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS gauges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  serial text NOT NULL, name text NOT NULL, material text, made_on date, made_by_machine_id uuid REFERENCES machines(id), made_by_operator text,
  in_service_at timestamptz, retired_at timestamptz, acceptance_criteria jsonb NOT NULL DEFAULT '{}', metadata jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS features (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), gauge_id uuid NOT NULL REFERENCES gauges(id) ON DELETE CASCADE,
  name text NOT NULL, nominal_mm double precision NOT NULL, lower_tol_mm double precision NOT NULL, upper_tol_mm double precision NOT NULL,
  feature_type text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS inspections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), gauge_id uuid NOT NULL REFERENCES gauges(id) ON DELETE CASCADE, machine_id uuid REFERENCES machines(id),
  operator text, inspected_at timestamptz NOT NULL DEFAULT now(), source_type text NOT NULL, source_name text, raw_record jsonb NOT NULL DEFAULT '{}',
  overall_result text, provenance jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS measurements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), inspection_id uuid NOT NULL REFERENCES inspections(id) ON DELETE CASCADE, feature_id uuid NOT NULL REFERENCES features(id) ON DELETE CASCADE,
  measured_mm double precision, measurement_uncertainty_mm double precision, method text NOT NULL, confidence text NOT NULL DEFAULT 'unknown', provenance jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS prediction_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, machine_id uuid REFERENCES machines(id), gauge_id uuid REFERENCES gauges(id),
  algorithm_version text NOT NULL, physics_version text NOT NULL, ml_model_version text, status text NOT NULL, prediction jsonb NOT NULL, uncertainty jsonb NOT NULL,
  assumptions jsonb NOT NULL DEFAULT '{}', provenance jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS calibration_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), machine_id uuid NOT NULL REFERENCES machines(id) ON DELETE CASCADE, feature_id uuid REFERENCES features(id), prediction_run_id uuid REFERENCES prediction_runs(id),
  predicted_mm double precision NOT NULL, measured_mm double precision NOT NULL, residual_mm double precision GENERATED ALWAYS AS (measured_mm - predicted_mm) STORED,
  context jsonb NOT NULL DEFAULT '{}', observed_at timestamptz NOT NULL DEFAULT now(), provenance jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS experiments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, machine_id uuid REFERENCES machines(id),
  hypothesis text NOT NULL, inputs jsonb NOT NULL DEFAULT '{}', predicted_information_gain double precision, actual_result jsonb,
  status text NOT NULL DEFAULT 'planned', conclusion text, created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz
);
CREATE TABLE IF NOT EXISTS provenance_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid REFERENCES projects(id) ON DELETE CASCADE, entity_type text NOT NULL, entity_id uuid,
  source_type text NOT NULL, source_ref text, payload jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS opportunity_graphs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, name text NOT NULL,
  status text NOT NULL DEFAULT 'active', objective text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS graph_nodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), graph_id uuid NOT NULL REFERENCES opportunity_graphs(id) ON DELETE CASCADE, node_type text NOT NULL,
  status text NOT NULL DEFAULT 'pending', label text NOT NULL, inputs jsonb NOT NULL DEFAULT '{}', outputs jsonb NOT NULL DEFAULT '{}', evidence jsonb NOT NULL DEFAULT '[]',
  confidence double precision, cost double precision, expected_value double precision, actual_value double precision, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS graph_edges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), graph_id uuid NOT NULL REFERENCES opportunity_graphs(id) ON DELETE CASCADE,
  from_node uuid NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE, to_node uuid NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE, condition jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS agent_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, agent_type text NOT NULL, status text NOT NULL,
  context_refs jsonb NOT NULL DEFAULT '[]', input jsonb NOT NULL DEFAULT '{}', output jsonb NOT NULL DEFAULT '{}', model text, created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz
);
CREATE TABLE IF NOT EXISTS loop_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, objective text NOT NULL,
  status text NOT NULL DEFAULT 'running', iteration integer NOT NULL DEFAULT 0, max_iterations integer NOT NULL DEFAULT 10, budget numeric, started_at timestamptz NOT NULL DEFAULT now(), ended_at timestamptz
);
CREATE TABLE IF NOT EXISTS ml_models (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, model_type text NOT NULL, version text NOT NULL,
  status text NOT NULL DEFAULT 'candidate', training_count integer NOT NULL DEFAULT 0, validation_metrics jsonb NOT NULL DEFAULT '{}', feature_schema jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS prediction_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, model_id uuid REFERENCES ml_models(id), prediction_run_id uuid REFERENCES prediction_runs(id),
  target text NOT NULL, predicted_value double precision, interval_low double precision, interval_high double precision, actual_value double precision, provenance jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS next_experiments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, machine_id uuid REFERENCES machines(id), hypothesis text NOT NULL,
  proposed_inputs jsonb NOT NULL, rationale jsonb NOT NULL, expected_information_gain double precision, uncertainty_target text, status text NOT NULL DEFAULT 'proposed', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS reverification_recommendations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), gauge_id uuid NOT NULL REFERENCES gauges(id) ON DELETE CASCADE, interval_days integer, status text NOT NULL,
  inputs jsonb NOT NULL DEFAULT '{}', evidence jsonb NOT NULL DEFAULT '{}', rationale text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS source_records (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, source_type text NOT NULL,
  filename text, content_hash text, raw_metadata jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS measurement_mappings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), source_record_id uuid NOT NULL REFERENCES source_records(id) ON DELETE CASCADE, source_column text NOT NULL,
  target_field text NOT NULL, confidence text NOT NULL DEFAULT 'unconfirmed', mapping_reason text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS geometry_assets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, filename text NOT NULL, format text NOT NULL,
  storage_path text, geometry_metadata jsonb NOT NULL DEFAULT '{}', extraction_status text NOT NULL DEFAULT 'pending', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS geometry_features (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), geometry_asset_id uuid NOT NULL REFERENCES geometry_assets(id) ON DELETE CASCADE, feature_type text NOT NULL, name text,
  nominal_mm double precision, axis text, bbox jsonb, extraction_method text NOT NULL, status text NOT NULL DEFAULT 'limited', provenance jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid REFERENCES projects(id) ON DELETE CASCADE, actor_type text NOT NULL, actor_id uuid,
  action text NOT NULL, entity_type text, entity_id uuid, details jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS production_drift_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, machine_id uuid NOT NULL REFERENCES machines(id), gauge_id uuid REFERENCES gauges(id), feature_id uuid REFERENCES features(id),
  predicted_mm double precision, measured_mm double precision NOT NULL, residual_mm double precision GENERATED ALWAYS AS (measured_mm - coalesce(predicted_mm, 0)) STORED,
  process_context jsonb NOT NULL DEFAULT '{}', observed_at timestamptz NOT NULL DEFAULT now(), provenance jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS service_wear_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, gauge_id uuid NOT NULL REFERENCES gauges(id), feature_id uuid REFERENCES features(id),
  measured_mm double precision NOT NULL, service_hours double precision, usage_count bigint, environment jsonb NOT NULL DEFAULT '{}', observed_at timestamptz NOT NULL DEFAULT now(), provenance jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS model_validation_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, model_id uuid REFERENCES ml_models(id), dataset_description text NOT NULL,
  n_train integer NOT NULL, n_validation integer NOT NULL, metrics jsonb NOT NULL DEFAULT '{}', calibration jsonb NOT NULL DEFAULT '{}', status text NOT NULL DEFAULT 'candidate', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS engineering_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, run_type text NOT NULL, input jsonb NOT NULL,
  deterministic_output jsonb, validation_output jsonb, uncertainty_output jsonb, status text NOT NULL DEFAULT 'completed', algorithm_version text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS import_batches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, source_record_id uuid REFERENCES source_records(id),
  status text NOT NULL DEFAULT 'preview', mapping jsonb NOT NULL DEFAULT '{}', row_count integer NOT NULL DEFAULT 0, accepted_count integer NOT NULL DEFAULT 0, rejected_count integer NOT NULL DEFAULT 0,
  errors jsonb NOT NULL DEFAULT '[]', created_at timestamptz NOT NULL DEFAULT now(), confirmed_at timestamptz
);
CREATE TABLE IF NOT EXISTS risk_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, geometry_asset_id uuid REFERENCES geometry_assets(id), feature_id uuid REFERENCES features(id), prediction_run_id uuid REFERENCES prediction_runs(id),
  risk_state text NOT NULL, predicted_deviation_mm double precision, interval_low_mm double precision, interval_high_mm double precision, tolerance_consumed_fraction double precision, reason text NOT NULL, provenance jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS system_identification_models (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, machine_id uuid REFERENCES machines(id), version text NOT NULL,
  feature_schema jsonb NOT NULL DEFAULT '{}', coefficients jsonb NOT NULL DEFAULT '{}', validation_metrics jsonb NOT NULL DEFAULT '{}', uncertainty jsonb NOT NULL DEFAULT '{}', observation_count integer NOT NULL DEFAULT 0, status text NOT NULL DEFAULT 'insufficient_data', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS agent_policies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, agent_type text NOT NULL, enabled boolean NOT NULL DEFAULT true,
  max_iterations integer NOT NULL DEFAULT 5, requires_approval boolean NOT NULL DEFAULT true, allowed_actions jsonb NOT NULL DEFAULT '[]', budget_limit numeric, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS engineering_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, loop_run_id uuid REFERENCES loop_runs(id), node_id uuid REFERENCES graph_nodes(id),
  decision text NOT NULL, evidence jsonb NOT NULL DEFAULT '{}', deterministic_score double precision, llm_judgment jsonb, approval_status text NOT NULL DEFAULT 'pending', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS inspection_exports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, gauge_id uuid REFERENCES gauges(id), format text NOT NULL,
  storage_path text, content_hash text, generated_from jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS inspection_imports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE, filename text NOT NULL, content_sha256 text NOT NULL,
  status text NOT NULL DEFAULT 'preview', column_mapping jsonb NOT NULL DEFAULT '{}', row_count integer NOT NULL DEFAULT 0, created_at timestamptz NOT NULL DEFAULT now(), confirmed_at timestamptz
);
CREATE TABLE IF NOT EXISTS data_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), key text NOT NULL UNIQUE, name text NOT NULL, category text NOT NULL, description text NOT NULL,
  collection_mode text NOT NULL, enabled boolean NOT NULL DEFAULT true, consent_required boolean NOT NULL DEFAULT true, proprietary_data_allowed boolean NOT NULL DEFAULT false,
  license_required boolean NOT NULL DEFAULT false, priority integer NOT NULL DEFAULT 50, config jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS data_observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid REFERENCES projects(id) ON DELETE CASCADE, source_id uuid REFERENCES data_sources(id), source_key text NOT NULL,
  observed_at timestamptz NOT NULL DEFAULT now(), entity_type text, entity_id uuid, event_type text NOT NULL, raw_payload jsonb NOT NULL DEFAULT '{}', normalized_payload jsonb NOT NULL DEFAULT '{}',
  provenance jsonb NOT NULL DEFAULT '{}', consent_state text NOT NULL DEFAULT 'unknown', validation_state text NOT NULL DEFAULT 'pending', quality_score double precision, content_hash text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS collection_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), source_id uuid REFERENCES data_sources(id), source_key text NOT NULL, started_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
  status text NOT NULL DEFAULT 'running', records_seen integer NOT NULL DEFAULT 0, records_accepted integer NOT NULL DEFAULT 0, records_rejected integer NOT NULL DEFAULT 0, error text, metadata jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS data_quality_checks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), observation_id uuid NOT NULL REFERENCES data_observations(id) ON DELETE CASCADE, check_name text NOT NULL,
  passed boolean NOT NULL, score double precision, details jsonb NOT NULL DEFAULT '{}', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS improvement_candidates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), project_id uuid REFERENCES projects(id) ON DELETE CASCADE, source_observation_id uuid REFERENCES data_observations(id),
  title text NOT NULL, hypothesis text NOT NULL, evidence jsonb NOT NULL DEFAULT '{}', target_component text NOT NULL, expected_impact double precision, risk_score double precision,
  status text NOT NULL DEFAULT 'candidate', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS flywheel_checkpoints (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), improvement_candidate_id uuid REFERENCES improvement_candidates(id) ON DELETE CASCADE,
  baseline_metrics jsonb NOT NULL DEFAULT '{}', experiment_metrics jsonb NOT NULL DEFAULT '{}', regression_metrics jsonb NOT NULL DEFAULT '{}', decision text NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS analytics_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid, session_id uuid, event_name text NOT NULL, event_time timestamptz NOT NULL DEFAULT now(),
  properties jsonb NOT NULL DEFAULT '{}', page text, source text, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS analytics_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid, started_at timestamptz NOT NULL DEFAULT now(), last_seen_at timestamptz NOT NULL DEFAULT now(), properties jsonb NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS profiles (
  id uuid PRIMARY KEY, display_name text, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);

-- High-value access paths. Avoid copying the old unused-index set wholesale.
CREATE INDEX IF NOT EXISTS projects_org_idx ON projects(organization_id, created_at DESC);
CREATE INDEX IF NOT EXISTS projects_owner_idx ON projects(owner_id, created_at DESC);
CREATE INDEX IF NOT EXISTS project_members_user_idx ON project_members(user_id, project_id);
CREATE INDEX IF NOT EXISTS machines_project_idx ON machines(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS gauges_project_idx ON gauges(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS features_gauge_idx ON features(gauge_id);
CREATE INDEX IF NOT EXISTS inspections_gauge_time_idx ON inspections(gauge_id, inspected_at DESC);
CREATE INDEX IF NOT EXISTS measurements_feature_time_idx ON measurements(feature_id, created_at DESC);
CREATE INDEX IF NOT EXISTS prediction_runs_project_time_idx ON prediction_runs(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS calibration_machine_feature_time_idx ON calibration_observations(machine_id, feature_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS agent_runs_project_time_idx ON agent_runs(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS engineering_runs_project_time_idx ON engineering_runs(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS audit_events_project_time_idx ON audit_events(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS production_drift_gauge_time_idx ON production_drift_observations(gauge_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS service_wear_gauge_time_idx ON service_wear_observations(gauge_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS data_observations_source_time_idx ON data_observations(source_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS data_observations_project_time_idx ON data_observations(project_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS collection_runs_source_time_idx ON collection_runs(source_id, started_at DESC);
CREATE INDEX IF NOT EXISTS improvement_candidates_project_time_idx ON improvement_candidates(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS analytics_events_time_idx ON analytics_events(event_time DESC);

-- Compatibility views retained during cutover.
CREATE OR REPLACE VIEW latest_prediction_trace AS
SELECT id, project_id, machine_id, gauge_id, algorithm_version, physics_version, ml_model_version, status, prediction, uncertainty, assumptions, provenance, created_at
FROM prediction_runs;

CREATE OR REPLACE VIEW feature_acceptance_status AS
SELECT f.id AS feature_id, f.gauge_id, f.name, f.nominal_mm, f.lower_tol_mm, f.upper_tol_mm,
       m.measured_mm, m.measurement_uncertainty_mm,
       CASE
         WHEN m.measured_mm IS NULL THEN jsonb_build_object('status','indeterminate','supported',false)
         WHEN f.lower_tol_mm >= 0 OR f.upper_tol_mm <= 0 OR f.nominal_mm + f.lower_tol_mm >= f.nominal_mm + f.upper_tol_mm THEN jsonb_build_object('status','invalid_tolerance','supported',false)
         WHEN m.measured_mm < f.nominal_mm + f.lower_tol_mm OR m.measured_mm > f.nominal_mm + f.upper_tol_mm THEN jsonb_build_object('status','fail','supported',true)
         WHEN abs(m.measured_mm - f.nominal_mm) / greatest(abs(f.lower_tol_mm),abs(f.upper_tol_mm)) >= 0.8 THEN jsonb_build_object('status','near_limit','supported',true)
         ELSE jsonb_build_object('status','pass','supported',true)
       END AS status
FROM features f
LEFT JOIN LATERAL (SELECT * FROM measurements m1 WHERE m1.feature_id=f.id ORDER BY m1.created_at DESC LIMIT 1) m ON true;

CREATE OR REPLACE VIEW gauge_drift_summary AS
SELECT g.id AS gauge_id, g.project_id, g.serial, g.name, g.material, g.made_on, g.made_by_machine_id,
       count(DISTINCT p.id) AS production_observation_count,
       count(DISTINCT w.id) AS service_wear_observation_count,
       max(p.observed_at) AS last_production_observation,
       max(w.observed_at) AS last_service_wear_observation,
       avg(p.residual_mm) AS production_mean_residual_mm,
       stddev_samp(p.residual_mm) AS production_residual_sd_mm
FROM gauges g
LEFT JOIN production_drift_observations p ON p.gauge_id=g.id
LEFT JOIN service_wear_observations w ON w.gauge_id=g.id
GROUP BY g.id;

CREATE OR REPLACE VIEW gauge_drift_service_separation AS
SELECT g.id AS gauge_id, g.project_id, g.serial, g.made_by_machine_id,
       coalesce(avg(abs(co.residual_mm)),0) AS production_drift_mean_abs_mm,
       coalesce(max(abs(co.residual_mm)),0) AS production_drift_max_abs_mm,
       coalesce(max(abs(m.measured_mm-f.nominal_mm)),0) AS service_wear_max_abs_mm
FROM gauges g
LEFT JOIN calibration_observations co ON co.machine_id=g.made_by_machine_id AND co.feature_id IN (SELECT id FROM features WHERE gauge_id=g.id)
LEFT JOIN features f ON f.gauge_id=g.id
LEFT JOIN measurements m ON m.feature_id=f.id
GROUP BY g.id, g.project_id, g.serial, g.made_by_machine_id;

COMMIT;

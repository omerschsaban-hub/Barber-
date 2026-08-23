# Fabrient PostgreSQL platform architecture

## Decision

Fabrient should use PostgreSQL as the authoritative application data plane. Supabase remains a migration source until authentication and storage have explicit replacements; it is not treated as the target architecture.

The current Supabase project is a PostgreSQL 17 database with 44 public tables, 4 public views, application functions, RLS, and a small amount of live data. The existing schema already contains the right engineering concepts, but it has accumulated many indexes that are currently unused. The rebuild keeps the proven domain model while making tenancy, auditability, migrations, and scale explicit.

## Product model

Fabrient serves three customer shapes with one core model:

- Individual: one organization, one or a few projects.
- Startup/team: organization members, project roles, shared engineering history.
- Enterprise: organization isolation, project-level authorization, audit history, service accounts/API keys, and predictable retention boundaries.

The hierarchy is:

`organization -> project -> engineering artifact/run -> verification -> manufacturing/inspection outcome`

Agents and MCP executions are first-class actors, not special database exceptions.

## Data domains

1. **Identity and tenancy** — organizations, memberships, projects, project members, service accounts.
2. **Engineering** — geometry assets/features, machines, gauges, design/engineering runs, experiments.
3. **Verification** — inspections, measurements, calibration observations, prediction runs, risk results.
4. **Manufacturing outcomes** — production drift, service wear, inspection imports/exports, acceptance decisions.
5. **Agents** — policies, agent runs, loop runs, decisions, execution/audit events.
6. **Data flywheel** — sources, observations, collection runs, quality checks, improvement candidates, checkpoints.
7. **Analytics** — sessions/events kept append-friendly and separately indexable.
8. **Artifacts** — large CAD/PDF/CSV files stay in object storage; PostgreSQL stores immutable metadata, hashes, and references.

## Scalability rules

- Every tenant-owned row is scoped by `organization_id` directly or through `project_id`.
- High-volume event tables are append-only and indexed by tenant plus time.
- JSONB is used for evidence/provenance payloads, not as a substitute for relational keys.
- No blanket indexing. Indexes are created from access patterns and measured query plans.
- Long-lived telemetry can be partitioned by time once volume justifies it.
- Engineering calculations remain deterministic and versioned; the database stores their inputs, outputs, versions, and provenance.
- Release/acceptance records are immutable after approval except through explicit superseding events.
- All schema changes are versioned SQL migrations in Git.

## Reliability

Production database changes are migration-only. The application never creates tables at runtime. Deploys run migrations before the application is marked healthy. Migration execution is idempotent and recorded in `schema_migrations`.

A database backup/restore drill is part of production acceptance. A green application build is not sufficient evidence that the database is healthy.

## Migration strategy

1. Preserve the current Supabase project as the rollback source.
2. Snapshot schema, functions, views, constraints, indexes, and all non-empty application data.
3. Provision Render PostgreSQL.
4. Apply the compatibility schema and then the new tenancy/audit extensions.
5. Import live application rows without changing UUIDs.
6. Run row-count, foreign-key, view, function, and representative workflow checks.
7. Switch application writes to Render PostgreSQL.
8. Keep Supabase read-only during the observation window.
9. Remove Supabase application data access only after production acceptance passes.

Do not delete the Supabase project as part of the initial cutover.

## Authentication and storage boundary

Authentication is deliberately not coupled to the database migration. Moving the data plane first prevents an auth rewrite from blocking the database rebuild. A later migration can move sessions/identity to a dedicated auth implementation while preserving user UUIDs.

CAD and generated manufacturing files must not be stored in PostgreSQL blobs. Use object storage with content hashes and immutable artifact records.

## Automation

The data-flywheel worker is a scheduled production workload. GitHub CI validates it, and Render runs the schedule independently of browser traffic. The schedule must be observable and idempotent: overlapping runs are prevented, every run gets a durable run record, and failures are visible.

The target cadence is every 30 minutes unless operational load requires a different interval.

## Acceptance standard

The database migration is complete only when the following chain works against Render PostgreSQL:

`human -> agent/MCP -> execution -> database write -> deterministic verification -> manufacturing outcome -> audit/provenance -> deployed runtime`

CI success alone does not count as database acceptance.

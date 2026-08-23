# Fabrient PostgreSQL migration

## Goal

Move Fabrient's application database from the current Supabase PostgreSQL instance to the Render PostgreSQL instance without losing the application schema or data, while keeping Supabase-managed control-plane data out of the standalone database.

The migration contract is:

1. **Source of truth during rehearsal:** the existing Supabase PostgreSQL database.
2. **Target:** the Render PostgreSQL database attached to the Fabrient workspace.
3. **Migrated:** the application `public` schema, including tables, views/materialized views, functions, triggers, constraints, indexes and table data.
4. **Not blindly migrated:** `auth`, `storage`, `realtime`, `vault`, and other Supabase-managed schemas. Auth and object storage require explicit provider cutover work rather than a raw database copy.
5. **Safety rule:** no destructive restore is allowed unless `ALLOW_DESTRUCTIVE_RESTORE=true` is explicitly set for the cutover invocation.
6. **Acceptance rule:** a migration is not considered successful until both the public-object manifest and exact public-table row counts match.

## Runtime contract

The cutover runner is `scripts/postgres_cutover.sh` and requires:

- `SOURCE_DATABASE_URL`: direct PostgreSQL connection string for the existing Supabase database.
- `TARGET_DATABASE_URL`: direct PostgreSQL connection string for the Render PostgreSQL database.

Optional:

- `VERIFY_ONLY=true` performs verification without restoring.
- `ALLOW_DESTRUCTIVE_RESTORE=true` enables `pg_restore --clean --if-exists`.
- `MIGRATION_WORKDIR=/path` changes the temporary working directory.

Never commit either connection string to the repository.

## Cutover sequence

### 1. Preflight

- Confirm the target PostgreSQL instance is healthy.
- Confirm the source is writable/available and no schema migration is running.
- Take/retain the normal provider backups before the final cutover.
- Freeze application writes for the final migration window.

### 2. Rehearsal

Run the script against a disposable target with destructive restore disabled. Repeat until the manifest and exact row counts match.

### 3. Application compatibility

Before switching traffic, all application database paths must use the target PostgreSQL connection rather than relying on Supabase's REST client for application data. Supabase Auth can remain the identity provider during an incremental cutover if required; it must not be treated as evidence that the application database migration is complete.

### 4. Final cutover

- Stop/disable write-producing workers.
- Run the migration with the production source and target URLs.
- Run `VERIFY_ONLY=true` once more against the same source/target pair.
- Switch the application to the target `DATABASE_URL`.
- Re-enable workers and scheduled jobs.
- Run end-to-end acceptance: auth/session, real database reads/writes, engineering loop, MCP calls, billing callbacks, storage paths, cron jobs and error recovery.

### 5. Rollback

Keep Supabase untouched until the target has passed production acceptance. Rollback means switching application reads/writes back to the source and stopping target writers; do not attempt an ad-hoc reverse merge while traffic is active.

## Why this is deliberately conservative

A green CI build is not proof of a database migration. The acceptance bar is the full chain:

**human/agent → application → database → deterministic engineering execution → verification → manufacturing outcome → deployed runtime**

The migration tooling therefore refuses to declare success based only on schema creation or a successful deploy.

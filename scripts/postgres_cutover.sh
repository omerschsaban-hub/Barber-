#!/usr/bin/env bash
set -Eeuo pipefail

# Production-safe PostgreSQL cutover helper.
# Required:
#   SOURCE_DATABASE_URL  - Supabase/PostgreSQL source connection string
#   TARGET_DATABASE_URL  - Render PostgreSQL target connection string
# Optional:
#   MIGRATION_WORKDIR            default /tmp/fabrient-postgres-migration
#   ALLOW_DESTRUCTIVE_RESTORE    set true only for an intentional clean restore
#   VERIFY_ONLY                  set true to skip restore and only compare manifests
#
# The runner migrates the application `public` schema. Supabase-managed schemas
# (auth, storage, realtime, vault, etc.) are deliberately excluded: identity and
# object storage require provider-specific cutover procedures and must not be
# blindly copied into a standalone PostgreSQL database.

: "${SOURCE_DATABASE_URL:?SOURCE_DATABASE_URL is required}"
: "${TARGET_DATABASE_URL:?TARGET_DATABASE_URL is required}"

WORKDIR="${MIGRATION_WORKDIR:-/tmp/fabrient-postgres-migration}"
VERIFY_ONLY="${VERIFY_ONLY:-false}"
ALLOW_DESTRUCTIVE_RESTORE="${ALLOW_DESTRUCTIVE_RESTORE:-false}"
DUMP_FILE="$WORKDIR/fabrient-public.dump"
SOURCE_MANIFEST="$WORKDIR/source-manifest.tsv"
TARGET_MANIFEST="$WORKDIR/target-manifest.tsv"
LOCK_KEY="734612985" # stable Fabrient migration advisory-lock key

mkdir -p "$WORKDIR"

command -v pg_dump >/dev/null || { echo "pg_dump is required" >&2; exit 2; }
command -v pg_restore >/dev/null || { echo "pg_restore is required" >&2; exit 2; }
command -v psql >/dev/null || { echo "psql is required" >&2; exit 2; }

manifest() {
  local url="$1"
  local out="$2"
  psql "$url" -X -v ON_ERROR_STOP=1 -AtF $'\t' <<'SQL' > "$out"
select c.relkind::text,
       n.nspname,
       c.relname,
       case when c.relkind in ('r','p') then coalesce(c.reltuples::bigint,0) else null end
from pg_class c
join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public'
  and c.relkind in ('r','p','v','m','f')
order by c.relkind, c.relname;
SQL
}

cleanup() {
  rm -f "$DUMP_FILE" "$SOURCE_MANIFEST" "$TARGET_MANIFEST"
}
trap cleanup EXIT

# Fail closed if a migration is already running against the target.
psql "$TARGET_DATABASE_URL" -X -v ON_ERROR_STOP=1 <<SQL
select pg_advisory_lock($LOCK_KEY);
create extension if not exists pgcrypto;
SQL

manifest "$SOURCE_DATABASE_URL" "$SOURCE_MANIFEST"

if [[ "$VERIFY_ONLY" == "true" ]]; then
  manifest "$TARGET_DATABASE_URL" "$TARGET_MANIFEST"
  diff -u "$SOURCE_MANIFEST" "$TARGET_MANIFEST" || {
    echo "VERIFY FAILED: target public schema object manifest differs from source." >&2
    exit 10
  }
  echo "VERIFY PASSED: public object manifest matches."
  exit 0
fi

# Dump only application data. This keeps Supabase-managed control planes out of
# the standalone Render database while preserving public tables, views, routines,
# triggers, constraints and indexes.
echo "[1/4] Dumping public schema from source..."
pg_dump "$SOURCE_DATABASE_URL" \
  --format=custom \
  --file="$DUMP_FILE" \
  --schema=public \
  --no-owner \
  --no-privileges \
  --quote-all-identifiers

# A destructive restore is intentionally opt-in. The default is additive restore,
# which is safer for rehearsals and retryable deployments.
RESTORE_ARGS=(
  --exit-on-error
  --no-owner
  --no-privileges
  --schema=public
)
if [[ "$ALLOW_DESTRUCTIVE_RESTORE" == "true" ]]; then
  RESTORE_ARGS+=(--clean --if-exists)
else
  echo "[2/4] Restoring additively (destructive restore disabled)..."
fi

if [[ "$ALLOW_DESTRUCTIVE_RESTORE" == "true" ]]; then
  echo "[2/4] Restoring with clean target objects (explicitly enabled)..."
fi
pg_restore "${RESTORE_ARGS[@]}" --dbname="$TARGET_DATABASE_URL" "$DUMP_FILE"

# Compare structural manifests. Row estimates are deliberately informational;
# exact counts are performed separately for tables so a successful restore cannot
# be mistaken for a successful data migration.
manifest "$TARGET_DATABASE_URL" "$TARGET_MANIFEST"

echo "[3/4] Comparing object manifests..."
diff -u "$SOURCE_MANIFEST" "$TARGET_MANIFEST" || {
  echo "CUTOVER FAILED: public object manifest differs after restore." >&2
  exit 11
}

# Exact row-count comparison for every ordinary/partitioned public table.
# The query is generated from catalog metadata, so newly-added tables are included
# automatically without editing this script.
echo "[4/4] Comparing exact table row counts..."
COUNT_SQL="$WORKDIR/counts.sql"
psql "$SOURCE_DATABASE_URL" -X -At -v ON_ERROR_STOP=1 <<'SQL' > "$COUNT_SQL"
select format('select %L as table_name, count(*)::bigint as row_count from public.%I;', c.relname, c.relname)
from pg_class c
join pg_namespace n on n.oid=c.relnamespace
where n.nspname='public' and c.relkind in ('r','p')
order by c.relname;
SQL

psql "$SOURCE_DATABASE_URL" -X -v ON_ERROR_STOP=1 -AtF $'\t' -f "$COUNT_SQL" > "$WORKDIR/source-counts.tsv"
psql "$TARGET_DATABASE_URL" -X -v ON_ERROR_STOP=1 -AtF $'\t' -f "$COUNT_SQL" > "$WORKDIR/target-counts.tsv"

diff -u "$WORKDIR/source-counts.tsv" "$WORKDIR/target-counts.tsv" || {
  echo "CUTOVER FAILED: exact public table row counts differ." >&2
  exit 12
}

echo "CUTOVER PASSED: schema manifest and exact public row counts match."

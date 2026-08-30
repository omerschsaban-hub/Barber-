BEGIN;

CREATE TABLE IF NOT EXISTS artifact_metadata (
  id UUID PRIMARY KEY,
  owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  project_id UUID NULL,
  filename TEXT NOT NULL CHECK (length(filename) BETWEEN 1 AND 255),
  content_type TEXT NOT NULL CHECK (length(content_type) BETWEEN 1 AND 255),
  size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0 AND size_bytes <= 25000000),
  sha256 TEXT NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS artifact_metadata_owner_created_idx ON artifact_metadata(owner_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS artifact_metadata_project_created_idx ON artifact_metadata(project_id, created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS artifact_data (
  artifact_id UUID PRIMARY KEY REFERENCES artifact_metadata(id) ON DELETE CASCADE,
  data BYTEA NOT NULL
);

INSERT INTO schema_migrations(version) VALUES ('011_postgres_artifacts') ON CONFLICT DO NOTHING;
COMMIT;

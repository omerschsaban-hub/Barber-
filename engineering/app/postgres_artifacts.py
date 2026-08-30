from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import BinaryIO

from .postgres import get_conn


@dataclass(frozen=True)
class Artifact:
    id: str
    owner_id: str
    project_id: str | None
    filename: str
    content_type: str
    size_bytes: int
    sha256: str


def ensure_schema() -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS artifact_metadata (
                    id UUID PRIMARY KEY,
                    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    project_id UUID NULL,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size_bytes BIGINT NOT NULL CHECK (size_bytes >= 0),
                    sha256 TEXT NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                CREATE INDEX IF NOT EXISTS idx_artifact_metadata_owner ON artifact_metadata(owner_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_artifact_metadata_project ON artifact_metadata(project_id, created_at DESC);
                CREATE TABLE IF NOT EXISTS artifact_data (
                    artifact_id UUID PRIMARY KEY REFERENCES artifact_metadata(id) ON DELETE CASCADE,
                    data BYTEA NOT NULL
                );
                """
            )
        conn.commit()


def put_bytes(*, artifact_id: str, owner_id: str, project_id: str | None, filename: str,
              content_type: str, data: bytes, max_bytes: int) -> Artifact:
    if len(data) > max_bytes:
        raise ValueError("artifact exceeds maximum allowed size")
    digest = hashlib.sha256(data).hexdigest()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO artifact_metadata(id, owner_id, project_id, filename, content_type, size_bytes, sha256)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (artifact_id, owner_id, project_id, filename, content_type, len(data), digest),
            )
            cur.execute("INSERT INTO artifact_data(artifact_id, data) VALUES (%s, %s)", (artifact_id, data))
        conn.commit()
    return Artifact(artifact_id, owner_id, project_id, filename, content_type, len(data), digest)


def get_metadata(artifact_id: str, owner_id: str) -> Artifact | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, owner_id, project_id, filename, content_type, size_bytes, sha256 FROM artifact_metadata WHERE id=%s AND owner_id=%s",
                (artifact_id, owner_id),
            )
            row = cur.fetchone()
    return Artifact(*row) if row else None


def get_bytes(artifact_id: str, owner_id: str) -> tuple[Artifact, BinaryIO] | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.id, m.owner_id, m.project_id, m.filename, m.content_type, m.size_bytes, m.sha256, d.data
                FROM artifact_metadata m JOIN artifact_data d ON d.artifact_id=m.id
                WHERE m.id=%s AND m.owner_id=%s
                """,
                (artifact_id, owner_id),
            )
            row = cur.fetchone()
    if not row:
        return None
    artifact = Artifact(*row[:7])
    import io
    return artifact, io.BytesIO(bytes(row[7]))

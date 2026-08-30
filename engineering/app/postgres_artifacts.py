from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import UUID

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
                (UUID(artifact_id), UUID(owner_id), UUID(project_id) if project_id else None, filename, content_type, len(data), digest),
            )
            cur.execute("INSERT INTO artifact_data(artifact_id, data) VALUES (%s, %s)", (UUID(artifact_id), data))
        conn.commit()
    return Artifact(artifact_id, owner_id, project_id, filename, content_type, len(data), digest)


def get_metadata(artifact_id: str, owner_id: str) -> Artifact | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id::text, owner_id::text, project_id::text, filename, content_type, size_bytes, sha256 FROM artifact_metadata WHERE id=%s AND owner_id=%s",
                (UUID(artifact_id), UUID(owner_id)),
            )
            row = cur.fetchone()
    return Artifact(*row) if row else None


def get_bytes(artifact_id: str, owner_id: str) -> tuple[Artifact, bytes] | None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.id::text, m.owner_id::text, m.project_id::text, m.filename, m.content_type, m.size_bytes, m.sha256, d.data
                FROM artifact_metadata m JOIN artifact_data d ON d.artifact_id=m.id
                WHERE m.id=%s AND m.owner_id=%s
                """,
                (UUID(artifact_id), UUID(owner_id)),
            )
            row = cur.fetchone()
    if not row:
        return None
    return Artifact(*row[:7]), bytes(row[7])

from __future__ import annotations

import hashlib
import os
import uuid

import pytest


pytestmark = pytest.mark.integration


def test_postgres_artifact_round_trip():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for PostgreSQL artifact integration test")

    from engineering.app.postgres_artifacts import ensure_schema, get_bytes, get_metadata, put_bytes

    ensure_schema()
    # This test intentionally exercises the storage abstraction without any external object-store credentials.
    from engineering.app.postgres import get_conn
    owner_id = str(uuid.uuid4())
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users(id, email) VALUES (%s, %s) ON CONFLICT DO NOTHING", (owner_id, f"artifact-test-{owner_id}@example.invalid"))
        conn.commit()

    payload = b"STEP test artifact\n"
    artifact_id = str(uuid.uuid4())
    result = put_bytes(
        artifact_id=artifact_id,
        owner_id=owner_id,
        project_id=None,
        filename="test.step",
        content_type="application/step",
        data=payload,
        max_bytes=1024,
    )
    assert result.sha256 == hashlib.sha256(payload).hexdigest()
    assert get_metadata(artifact_id, owner_id).size_bytes == len(payload)
    stored = get_bytes(artifact_id, owner_id)
    assert stored is not None
    assert stored[1].read() == payload

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id=%s", (owner_id,))
        conn.commit()

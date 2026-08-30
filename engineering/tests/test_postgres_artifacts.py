from __future__ import annotations

import hashlib
import os
import uuid

import pytest

pytestmark = pytest.mark.integration


def test_postgres_artifact_round_trip():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL required for PostgreSQL artifact integration test")

    from engineering.app.postgres_artifacts import get_bytes, get_metadata, put_bytes
    from engineering.app.postgres import get_conn

    owner_id = str(uuid.uuid4())
    email = f"artifact-test-{owner_id}@example.invalid"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users(id, email) VALUES (%s, %s)", (owner_id, email))
        conn.commit()

    try:
        payload = b"STEP test artifact\n"
        artifact_id = str(uuid.uuid4())
        result = put_bytes(artifact_id=artifact_id, owner_id=owner_id, project_id=None,
                           filename="test.step", content_type="application/step",
                           data=payload, max_bytes=1024)
        assert result.sha256 == hashlib.sha256(payload).hexdigest()
        metadata = get_metadata(artifact_id, owner_id)
        assert metadata is not None and metadata.size_bytes == len(payload)
        stored = get_bytes(artifact_id, owner_id)
        assert stored is not None
        assert stored[1] == payload
        assert get_metadata(artifact_id, str(uuid.uuid4())) is None
    finally:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id=%s", (owner_id,))
            conn.commit()

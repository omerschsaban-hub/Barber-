import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[2]


def apply(conn, rel: str) -> None:
    conn.execute((ROOT / rel).read_text(encoding="utf-8"))


def test_legacy_platform_schema_reconciles_to_owned_auth_contract():
    dsn = os.environ["DATABASE_URL"]
    with psycopg.connect(dsn) as conn:
        with conn.transaction():
            apply(conn, "db/migrations/0001_platform_auth.sql")
            apply(conn, "db/migrations/001_owned_postgres.sql")
            apply(conn, "db/migrations/010_schema_reconciliation.sql")

        rows = conn.execute(
            """select table_name, column_name
               from information_schema.columns
               where table_schema='public'
                 and ((table_name='users' and column_name in ('role','email_verified_at'))
                   or (table_name='oauth_clients' and column_name in ('client_name','public_client'))
                   or (table_name='billing_entitlements' and column_name in ('active','source'))
                   or (table_name='billing_events' and column_name in ('occurred_at','sequence_number')))"""
        ).fetchall()
        actual = {(row[0], row[1]) for row in rows}

    expected = {
        ("users", "role"),
        ("users", "email_verified_at"),
        ("oauth_clients", "client_name"),
        ("oauth_clients", "public_client"),
        ("billing_entitlements", "active"),
        ("billing_entitlements", "source"),
        ("billing_events", "occurred_at"),
        ("billing_events", "sequence_number"),
    }
    assert expected <= actual

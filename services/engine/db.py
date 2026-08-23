"""Small, audited PostgreSQL data-access layer for the engineering service."""
from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Any

from psycopg import Connection, connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


def qi(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


class PostgresClient:
    def __init__(self) -> None:
        self.url = os.getenv("DATABASE_URL", "").strip()
        if not self.url:
            raise RuntimeError("DATABASE_URL is not configured")

    @contextmanager
    def connection(self):
        conn: Connection = connect(self.url, row_factory=dict_row, connect_timeout=10)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get(self, table: str, params: dict[str, str] | None = None) -> list[dict[str, Any]]:
        params = params or {}
        selected = params.get("select", "*")
        columns = "*" if selected == "*" else ",".join(qi(c.strip()) for c in selected.split(","))
        sql = f"select {columns} from {qi(table)}"
        values: list[Any] = []
        filters: list[str] = []
        for key, raw in params.items():
            if key in {"select", "order", "limit"} or key == "offset":
                continue
            if raw.startswith("eq."):
                filters.append(f"{qi(key)} = %s")
                value = raw[3:]
                if value == "true": value = True
                elif value == "false": value = False
                values.append(value)
        if filters:
            sql += " where " + " and ".join(filters)
        order = params.get("order")
        if order:
            pieces = []
            for item in order.split(","):
                parts = item.split(".")
                pieces.append(f"{qi(parts[0])} {'desc' if len(parts) > 1 and parts[1].lower() == 'desc' else 'asc'}")
            sql += " order by " + ",".join(pieces)
        if params.get("limit"):
            sql += " limit %s"; values.append(int(params["limit"]))
        if params.get("offset"):
            sql += " offset %s"; values.append(int(params["offset"]))
        with self.connection() as conn:
            return list(conn.execute(sql, values).fetchall())

    def insert(self, table: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        columns = list(payload)
        values = [Jsonb(v) if isinstance(v, (dict, list)) else v for v in payload.values()]
        sql = f"insert into {qi(table)} ({','.join(qi(c) for c in columns)}) values ({','.join(['%s'] * len(values))}) returning *"
        with self.connection() as conn:
            return list(conn.execute(sql, values).fetchall())

    def patch(self, table: str, filters: dict[str, str], payload: dict[str, Any]) -> None:
        sets = []
        values: list[Any] = []
        for column, value in payload.items():
            sets.append(f"{qi(column)} = %s")
            values.append(Jsonb(value) if isinstance(value, (dict, list)) else value)
        where = []
        for column, raw in filters.items():
            if not raw.startswith("eq."):
                raise ValueError("Only eq filters are supported")
            where.append(f"{qi(column)} = %s")
            values.append(raw[3:])
        sql = f"update {qi(table)} set {','.join(sets)} where {' and '.join(where)}"
        with self.connection() as conn:
            conn.execute(sql, values)

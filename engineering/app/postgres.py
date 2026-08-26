from __future__ import annotations
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
ROOT=Path(__file__).resolve().parents[2]
SCHEMA=ROOT/'db'/'migrations'/'001_owned_postgres.sql'
_POOL: ConnectionPool|None=None
def pool()->ConnectionPool:
 global _POOL
 if _POOL is None:
  dsn=os.environ['DATABASE_URL']
  if os.getenv('ENVIRONMENT','production')=='production' and 'sslmode=' not in dsn: raise RuntimeError('DATABASE_URL must specify sslmode for production')
  _POOL=ConnectionPool(conninfo=dsn,min_size=int(os.getenv('DB_POOL_MIN','1')),max_size=int(os.getenv('DB_POOL_MAX','8')),kwargs={'row_factory':dict_row},open=True)
 return _POOL
@contextmanager
def transaction()->Iterator[Any]:
 with pool().connection() as conn:
  with conn.transaction(): yield conn
def ensure_schema()->None:
 with transaction() as conn: conn.execute(SCHEMA.read_text(encoding='utf-8'))
def fetch_all(sql:str,params:tuple[Any,...]=())->list[dict[str,Any]]:
 with pool().connection() as conn: return list(conn.execute(sql,params).fetchall())
def fetch_one(sql:str,params:tuple[Any,...]=())->dict[str,Any]|None:
 with pool().connection() as conn: return conn.execute(sql,params).fetchone()
def execute(sql:str,params:tuple[Any,...]=())->None:
 with pool().connection() as conn: conn.execute(sql,params)
def close_pool()->None:
 global _POOL
 if _POOL is not None: _POOL.close(); _POOL=None

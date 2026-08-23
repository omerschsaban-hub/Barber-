import { Pool, type QueryResultRow } from 'pg';

let pool: Pool | undefined;

export function hasPostgresConfig() {
  return Boolean(process.env.DATABASE_URL);
}

export function getPostgresPool() {
  if (!process.env.DATABASE_URL) {
    throw new Error('DATABASE_URL is not configured');
  }
  if (!pool) {
    pool = new Pool({
      connectionString: process.env.DATABASE_URL,
      max: Number(process.env.DB_POOL_MAX || 10),
      idleTimeoutMillis: 30_000,
      connectionTimeoutMillis: 5_000,
      maxLifetimeSeconds: 300,
      ssl: process.env.DATABASE_SSL === 'false' ? false : { rejectUnauthorized: false },
    });
  }
  return pool;
}

export async function query<T extends QueryResultRow = QueryResultRow>(text: string, values?: unknown[]) {
  return getPostgresPool().query<T>(text, values);
}

export async function closePostgresPool() {
  if (pool) {
    await pool.end();
    pool = undefined;
  }
}

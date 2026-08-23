import pg from "pg";
const { Client } = pg;
if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
const client = new Client({ connectionString: process.env.DATABASE_URL, ssl: { rejectUnauthorized: false } });
await client.connect();
try {
  const version = await client.query("select version() as version");
  const tables = await client.query("select count(*)::int as count from information_schema.tables where table_schema='public'");
  console.log(JSON.stringify({ ok: true, postgres: version.rows[0].version, public_tables: tables.rows[0].count }));
} finally { await client.end(); }

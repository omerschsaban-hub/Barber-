import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import pg from "pg";

const { Client } = pg;
const url = process.env.DATABASE_URL;
if (!url) throw new Error("DATABASE_URL is required for PostgreSQL migrations");

const client = new Client({
  connectionString: url,
  ssl: process.env.DATABASE_SSL === "false" ? false : { rejectUnauthorized: false },
  connectionTimeoutMillis: 10_000,
});

await client.connect();
try {
  await client.query("select pg_advisory_lock(hashtext('fabrient:migrations'))");
  await client.query(`
    create table if not exists schema_migrations (
      version text primary key,
      applied_at timestamptz not null default now(),
      checksum text not null
    )
  `);

  const dir = join(process.cwd(), "db", "migrations");
  const files = (await readdir(dir)).filter((f) => f.endsWith(".sql")).sort();

  for (const file of files) {
    const version = file.replace(/\.sql$/, "");
    const sql = await readFile(join(dir, file), "utf8");
    const existing = await client.query("select checksum from schema_migrations where version=$1", [version]);
    const checksum = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(sql));
    const digest = Buffer.from(checksum).toString("hex");

    if (existing.rowCount) {
      if (existing.rows[0].checksum !== digest) throw new Error(`Migration checksum changed: ${file}`);
      continue;
    }

    await client.query(sql);
    await client.query("insert into schema_migrations(version, checksum) values($1,$2)", [version, digest]);
    console.log(`applied ${file}`);
  }
} finally {
  await client.query("select pg_advisory_unlock(hashtext('fabrient:migrations'))").catch(() => {});
  await client.end();
}

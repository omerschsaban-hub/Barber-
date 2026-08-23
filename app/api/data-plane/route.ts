import { NextResponse } from "next/server";
import { Pool } from "pg";

export const dynamic = "force-dynamic";

let pool: Pool | undefined;
function db() {
  if (!process.env.DATABASE_URL) throw new Error("DATABASE_URL is required");
  pool ??= new Pool({ connectionString: process.env.DATABASE_URL, max: Number(process.env.DB_POOL_MAX || 10), idleTimeoutMillis: 30000 });
  return pool;
}

export async function GET() {
  try {
    const result = await db().query("select current_database() as database, now() as server_time");
    return NextResponse.json({ ok: true, dataPlane: "postgresql", ...result.rows[0] });
  } catch (error) {
    return NextResponse.json({ ok: false, error: error instanceof Error ? error.message : "database unavailable" }, { status: 503 });
  }
}

import { NextResponse } from "next/server";
import { Pool } from "pg";

export const dynamic = "force-dynamic";

export async function GET() {
  if (!process.env.DATABASE_URL) {
    return NextResponse.json({ ok: false, dataPlane: "unconfigured" }, { status: 503 });
  }

  const pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 3, connectionTimeoutMillis: 3000 });
  try {
    const result = await pool.query("select now() as now");
    return NextResponse.json({ ok: true, dataPlane: "postgresql", databaseTime: result.rows[0]?.now });
  } catch (error) {
    return NextResponse.json({ ok: false, dataPlane: "postgresql", error: error instanceof Error ? error.message : "database unavailable" }, { status: 503 });
  } finally {
    await pool.end();
  }
}

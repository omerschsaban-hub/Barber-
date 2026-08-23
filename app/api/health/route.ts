import { NextResponse } from 'next/server';
import { hasPostgresConfig, query } from '@/lib/postgres';

export const dynamic = 'force-dynamic';

export async function GET() {
  const started = Date.now();
  if (!hasPostgresConfig()) {
    return NextResponse.json({ ok: false, database: 'not_configured' }, { status: 503 });
  }

  try {
    const result = await query<{ ok: number; now: string; database: string }>(
      'select 1 as ok, now()::text as now, current_database() as database',
    );
    return NextResponse.json({
      ok: result.rows[0]?.ok === 1,
      database: result.rows[0]?.database,
      latency_ms: Date.now() - started,
    });
  } catch (error) {
    return NextResponse.json(
      { ok: false, database: 'unreachable', error: error instanceof Error ? error.message : 'database error' },
      { status: 503 },
    );
  }
}

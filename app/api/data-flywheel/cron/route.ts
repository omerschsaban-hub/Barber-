import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 300;

function workerUrl() {
  const configured = process.env.DATA_FLYWHEEL_WORKER_URL;
  if (configured) return configured.replace(/\/$/, "") + "/data-flywheel/worker";
  const base = process.env.NEXT_PUBLIC_APP_URL || process.env.VERCEL_URL;
  if (!base) throw new Error("DATA_FLYWHEEL_WORKER_URL or VERCEL_URL is required");
  return `${base.startsWith("http") ? base : `https://${base}`}/data-flywheel/worker`;
}

export async function GET(request: Request) {
  const auth = request.headers.get("authorization");
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && auth !== `Bearer ${cronSecret}`) {
    return NextResponse.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 240_000);
  try {
    const response = await fetch(workerUrl(), {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(process.env.DATA_FLYWHEEL_INGEST_SECRET
          ? { "x-fabrient-ingest-secret": process.env.DATA_FLYWHEEL_INGEST_SECRET }
          : {}),
      },
      body: JSON.stringify({ trigger: "vercel-cron", scheduled: true }),
      cache: "no-store",
      signal: controller.signal,
    });
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: { "content-type": response.headers.get("content-type") || "application/json" },
    });
  } catch (error) {
    return NextResponse.json(
      { ok: false, error: error instanceof Error ? error.message : "worker invocation failed" },
      { status: 502 },
    );
  } finally {
    clearTimeout(timer);
  }
}

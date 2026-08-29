import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const maxDuration = 300;

function workerUrl() {
  const configured = process.env.DATA_FLYWHEEL_WORKER_URL || process.env.FABRIENT_API_URL || process.env.NEXT_PUBLIC_ENGINEERING_API;
  if (!configured) throw new Error("DATA_FLYWHEEL_WORKER_URL or FABRIENT_API_URL is required");
  return configured.replace(/\/$/, "") + "/internal/data-flywheel/run";
}

export async function GET(request: Request) {
  const auth = request.headers.get("authorization");
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && auth !== `Bearer ${cronSecret}`) {
    return NextResponse.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }

  const runToken = process.env.DATA_FLYWHEEL_RUN_TOKEN;
  if (!runToken) {
    return NextResponse.json({ ok: false, error: "DATA_FLYWHEEL_RUN_TOKEN is not configured" }, { status: 503 });
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 240_000);
  try {
    const response = await fetch(`${workerUrl()}?token=${encodeURIComponent(runToken)}`, {
      method: "GET",
      headers: { "cache-control": "no-store" },
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

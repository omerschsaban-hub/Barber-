'use client';

/** Non-blocking, privacy-preserving product telemetry.
 * Never captures request bodies, headers, tokens, URLs with query strings, or private content.
 * Telemetry must never be on the critical rendering path.
 */
const QUEUE_KEY = 'fabrient:telemetry:v1';
const MAX_QUEUE = 100;

type TelemetryEvent = {
  name: string;
  ts: string;
  path: string;
  duration_ms?: number;
  ok?: boolean;
  status?: number;
  metadata?: Record<string, string | number | boolean | null>;
};

function safePath(): string {
  try { return window.location.pathname; } catch { return '/'; }
}

function readQueue(): TelemetryEvent[] {
  try { return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]'); } catch { return []; }
}

function writeQueue(events: TelemetryEvent[]) {
  try { localStorage.setItem(QUEUE_KEY, JSON.stringify(events.slice(-MAX_QUEUE))); } catch {}
}

export function trackProductEvent(name: string, metadata?: TelemetryEvent['metadata']) {
  try {
    if (!name || name.length > 80) return;
    const event: TelemetryEvent = { name, ts: new Date().toISOString(), path: safePath(), metadata };
    writeQueue([...readQueue(), event]);
    flushTelemetry();
  } catch {}
}

export function trackApiOutcome(name: string, duration_ms: number, ok: boolean, status?: number) {
  trackProductEvent(name, { duration_ms: Math.round(Math.max(0, duration_ms)), ok, status: status ?? null });
}

let flushing = false;
export function flushTelemetry() {
  if (flushing || typeof navigator === 'undefined' || !navigator.onLine) return;
  const events = readQueue();
  if (!events.length) return;
  flushing = true;
  const payload = JSON.stringify({ events });
  try {
    const accepted = navigator.sendBeacon?.('/api/telemetry', new Blob([payload], { type: 'application/json' }));
    if (accepted) writeQueue([]);
  } catch {}
  flushing = false;
}

'use client';

/**
 * Non-blocking, privacy-preserving product telemetry.
 * Never captures request bodies, headers, tokens, query strings, private content,
 * keystrokes, or precise location. Telemetry is best-effort and cannot block UI.
 */
const QUEUE_KEY = 'fabrient:telemetry:v2';
const MAX_QUEUE = 200;
const SESSION_KEY = 'fabrient:telemetry:session';

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
  try { return window.location.pathname || '/'; } catch { return '/'; }
}

function sessionId(): string {
  try {
    const existing = sessionStorage.getItem(SESSION_KEY);
    if (existing) return existing;
    const id = crypto.randomUUID();
    sessionStorage.setItem(SESSION_KEY, id);
    return id;
  } catch { return 'ephemeral'; }
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
    const event: TelemetryEvent = {
      name,
      ts: new Date().toISOString(),
      path: safePath(),
      metadata: { session: sessionId(), ...metadata },
    };
    writeQueue([...readQueue(), event]);
    flushTelemetry();
  } catch {}
}

export function trackApiOutcome(name: string, duration_ms: number, ok: boolean, status?: number) {
  trackProductEvent(name, {
    duration_ms: Math.round(Math.max(0, duration_ms)),
    ok,
    status: status ?? null,
  });
}

export function trackWorkflowEvent(
  workflow: string,
  event: 'started' | 'completed' | 'abandoned' | 'failed',
  metadata?: TelemetryEvent['metadata'],
) {
  trackProductEvent(`workflow.${event}`, { workflow, ...metadata });
}

export function trackPerformanceMetric(
  metric: 'navigation' | 'paint' | 'interaction' | 'resource',
  value_ms: number,
) {
  trackProductEvent(`performance.${metric}`, { value_ms: Math.round(Math.max(0, value_ms)) });
}

let flushing = false;
export function flushTelemetry() {
  if (flushing || typeof navigator === 'undefined' || !navigator.onLine) return;
  const events = readQueue();
  if (!events.length) return;
  flushing = true;
  try {
    const payload = JSON.stringify({ events });
    const accepted = navigator.sendBeacon?.(
      '/api/telemetry',
      new Blob([payload], { type: 'application/json' }),
    );
    if (accepted) writeQueue([]);
  } catch {}
  flushing = false;
}

'use client';

import { useEffect } from 'react';
import { loadLocalLoop, saveLoop } from '@/lib/engineering-loop';
import { trackApiOutcome, flushTelemetry } from '@/lib/product-telemetry';

const SAFE_ENDPOINTS = ['/v1/predict', '/v1/import/preview', '/v1/reverification'];

export default function EngineeringLoopTracker() {
  useEffect(() => {
    let active = true;
    const original = window.fetch.bind(window);

    const track = async (input: RequestInfo | URL, init?: RequestInit) => {
      const started = performance.now();
      let response: Response;
      try {
        response = await original(input, init);
      } catch (error) {
        trackApiOutcome('api.request.error', performance.now() - started, false);
        throw error;
      }

      // Telemetry/learning is strictly best-effort and only inspects approved endpoints.
      try {
        const rawUrl = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
        const path = new URL(rawUrl, window.location.origin).pathname;
        trackApiOutcome(`api.${response.ok ? 'success' : 'failure'}`, performance.now() - started, response.ok, response.status);
        if (!SAFE_ENDPOINTS.some((endpoint) => path.includes(endpoint))) return response;
        const clone = response.clone();
        const data = await clone.json().catch(() => null);
        if (!active || !data) return response;
        const previous = loadLocalLoop();
        let next: any = null;
        if (path.includes('/v1/predict') && response.ok) next = { stage: 'review', status: 'ready', next_action: 'Review the verified prediction and decide whether to move to build.', last_action: 'Completed deterministic prediction', evidence_summary: { prediction: data.prediction_mm, interval: data.interval_95_mm } };
        else if (path.includes('/v1/import/preview') && response.ok) next = { stage: 'inspect', status: 'ready', next_action: 'Confirm the inspection mapping and ingest real measurements.', last_action: 'Previewed inspection record', evidence_summary: { import_rows: data.row_count_preview, sha256: data.content_sha256 } };
        else if (path.includes('/v1/reverification') && response.ok) next = { stage: 'reverify', status: data.interval_days ? 'ready' : 'blocked', next_action: data.interval_days ? 'Run the next physical verification when the interval is reached.' : 'Do not release: no defensible re-verification interval exists.', last_action: 'Calculated re-verification interval', evidence_summary: { reverification: data } };
        if (next) {
          const merged = { ...previous, ...next };
          try { saveLoop(merged); window.dispatchEvent(new CustomEvent('fabrient:loop-updated', { detail: merged })); } catch {}
        }
      } catch {}
      return response;
    };

    window.fetch = track as typeof window.fetch;
    const onOnline = () => flushTelemetry();
    window.addEventListener('online', onOnline);
    flushTelemetry();
    return () => { active = false; window.fetch = original; window.removeEventListener('online', onOnline); };
  }, []);
  return null;
}

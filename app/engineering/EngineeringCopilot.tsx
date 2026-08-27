'use client';

import {FormEvent, useState} from 'react';

type Result = {
  status?: string;
  error?: string;
  usage?: {used?: number; limit?: number; message?: string};
  intent?: {
    operation?: string;
    intent_summary?: string;
    entity?: string | null;
    resolved_dimensions_mm?: {width: number | null; height: number | null; depth: number | null} | null;
    evidence_sources?: string[];
    missing_information?: string[];
    confidence?: number;
  };
  engineering?: any;
  layers?: any;
};

export default function EngineeringCopilot() {
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Result | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setResult(null);
    try {
      const response = await fetch('/api/engineering-intent', {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({naturalLanguage: text, execute: true}),
      });
      const body = await response.json();
      setResult(response.ok ? body : {status: body.status || 'Request blocked', error: body.error || 'Request failed', usage: body.usage});
    } catch (error: any) {
      setResult({status: 'failed', error: error?.message || 'Request failed'});
    } finally {
      setBusy(false);
    }
  }

  const dims = result?.intent?.resolved_dimensions_mm;
  const missing = result?.intent?.missing_information || [];

  return <section className="panel" style={{marginTop:24, border: '1px solid rgba(120,160,255,.35)'}}>
    <div className="eyebrow">FABRIENT / NATURAL LANGUAGE ENGINEERING</div>
    <h2 style={{marginBottom:8}}>Just tell Fabrient what you mean.</h2>
    <p className="muted">No engineering numbers are required when the thing itself identifies the target. Fabrient resolves the intent, finds missing product facts when appropriate, then hands the actual engineering calculation to the deterministic engine and ML models.</p>
    <form onSubmit={submit} style={{display:'grid', gap:10}}>
      <textarea
        rows={3}
        value={input}
        onChange={e=>setInput(e.target.value.slice(0,12000))}
        placeholder="Example: Check the expected fit for an iPhone 19 enclosure in PETG on Machine 01"
        aria-label="Describe what you want Fabrient to engineer"
      />
      <button className="button primary" disabled={busy || !input.trim()} type="submit">
        {busy ? 'Understanding → verifying…' : 'Run with Fabrient'}
      </button>
    </form>

    {result && <div className="panel" style={{marginTop:14}}>
      <div className="row" style={{justifyContent:'space-between'}}>
        <strong>{result.status || 'Result'}</strong>
        {result.intent?.confidence !== undefined && <span className="status ok">LLM confidence {Math.round(result.intent.confidence * 100)}%</span>}
      </div>
      {result.intent?.intent_summary && <p>{result.intent.intent_summary}</p>}
      {result.intent?.entity && <p><strong>Understood target:</strong> {result.intent.entity}</p>}
      {dims && <p><strong>Resolved physical envelope:</strong> {dims.width ?? '—'} × {dims.height ?? '—'} × {dims.depth ?? '—'} mm</p>}
      {missing.length > 0 && <div><strong>Still needed:</strong><ul>{missing.map((item, i)=><li key={`${item}-${i}`}>{item}</li>)}</ul></div>}
      {result.intent?.evidence_sources?.length ? <details><summary>Product evidence</summary><ul>{result.intent.evidence_sources.map((url, i)=><li key={`${url}-${i}`}><a href={url} target="_blank" rel="noreferrer">{url}</a></li>)}</ul></details> : null}
      {result.usage?.message && <p className="muted small">{result.usage.message}</p>}
      {result.engineering && <details style={{marginTop:8}}><summary>Engineering evidence</summary><pre className="provenance">{JSON.stringify(result.engineering, null, 2)}</pre></details>}
      <details style={{marginTop:8}}><summary>Pipeline used</summary><pre className="provenance">{JSON.stringify(result.layers, null, 2)}</pre></details>
      {result.error && <p className="error">{result.error}</p>}
    </div>}
  </section>;
}

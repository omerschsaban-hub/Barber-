'use client';

import { useState } from 'react';

const providers = [
  { id: 'autodesk_fusion', name: 'Autodesk Fusion', description: 'Connect an authorized Fusion MCP endpoint.' },
  { id: 'propel_plm', name: 'Propel PLM', description: 'Connect an authorized Propel MCP endpoint.' },
];

export default function IntegrationsPage() {
  const [provider, setProvider] = useState(providers[0].id);
  const [endpoint, setEndpoint] = useState('');
  const [token, setToken] = useState('');
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);

  async function connect() {
    setBusy(true); setStatus('Connecting…');
    try {
      const r = await fetch('/integrations/connect', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ provider, endpoint, bearer_token: token || null }) });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'Connection failed');
      setStatus(`Connected. ${data.tool_count ?? 0} tools discovered.`);
      setToken('');
    } catch (e) { setStatus(e instanceof Error ? e.message : 'Connection failed'); }
    finally { setBusy(false); }
  }

  return <main className="page-shell">
    <h1>Integrations</h1>
    <p>Connect Fabrient to engineering systems you already use through their authorized MCP interface.</p>
    <section className="card">
      <label>System<select value={provider} onChange={e => setProvider(e.target.value)}>{providers.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
      <p>{providers.find(p => p.id === provider)?.description}</p>
      <label>MCP endpoint<input value={endpoint} onChange={e => setEndpoint(e.target.value)} placeholder="https://…" autoComplete="off" /></label>
      <label>Bearer token (optional)<input type="password" value={token} onChange={e => setToken(e.target.value)} placeholder="Token" autoComplete="new-password" /></label>
      <button disabled={busy || !endpoint} onClick={connect}>{busy ? 'Connecting…' : 'Connect & test'}</button>
      {status && <p role="status">{status}</p>}
    </section>
  </main>;
}

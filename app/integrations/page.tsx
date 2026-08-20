'use client';
import { useEffect, useState } from 'react';

type Provider = { id: string; name: string; description: string; auth: string; endpoint: string; docs: string; configured?: boolean; kind?: string };
type Tool = { provider: string; name?: string; description?: string };

export default function IntegrationsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [query, setQuery] = useState('');
  const [toolQuery, setToolQuery] = useState('');
  const [tools, setTools] = useState<Tool[]>([]);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState<string | null>(null);

  async function load(q = '') {
    const r = await fetch(`/integrations/search?query=${encodeURIComponent(q)}`);
    const data = await r.json();
    setProviders(data.results || []);
  }

  useEffect(() => { load(); }, []);
  useEffect(() => { const t = setTimeout(() => load(query), 180); return () => clearTimeout(t); }, [query]);
  useEffect(() => {
    const t = setTimeout(async () => {
      const r = await fetch(`/integrations/search-tools?query=${encodeURIComponent(toolQuery)}`);
      const data = await r.json();
      setTools(data.tools || []);
    }, 250);
    return () => clearTimeout(t);
  }, [toolQuery]);

  async function connect(p: Provider) {
    setBusy(p.id); setStatus('');
    try {
      const r = await fetch('/integrations/auth/start', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ provider: p.id }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'Unable to start connection');
      if (data.auth_url) {
        window.open(data.auth_url, '_blank', 'noopener,noreferrer');
        setStatus(`${p.name}: official MCP endpoint opened.`);
      } else {
        if (data.docs) window.open(data.docs, '_blank', 'noopener,noreferrer');
        setStatus(`${p.name}: use the provider's official MCP authorization flow.`);
      }
    } catch(e) {
      setStatus(e instanceof Error ? e.message : 'Connection failed');
    } finally { setBusy(null); }
  }

  return <main className="page-shell">
    <h1>Connect your tools</h1>
    <p>Fabrient only lists MCP integrations with a verified, vendor-published MCP endpoint.</p>
    <section className="card">
      <input aria-label="Search integrations" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search CAD, PLM, documentation, repositories…" />
    </section>
    <section className="grid">
      {providers.map(p=><article className="card" key={p.id}>
        <h2>{p.name}</h2>
        <p>{p.description}</p>
        <small>{p.kind?.replaceAll('_',' ')}</small>
        <div><button disabled={busy===p.id} onClick={()=>connect(p)}>{busy===p.id?'Opening…':p.configured?'Connected':'Connect'}</button></div>
      </article>)}
    </section>
    <section className="card">
      <h2>Find a tool for the job</h2>
      <p>Search what you need done; Fabrient searches the live tool names and descriptions from connected official MCP servers.</p>
      <input aria-label="Search connected tools" value={toolQuery} onChange={e=>setToolQuery(e.target.value)} placeholder="e.g. search documentation, inspect repository" />
      {tools.length>0&&<ul>{tools.map((t,i)=><li key={`${t.provider}-${t.name}-${i}`}><strong>{t.name}</strong> — {t.description} <small>({t.provider})</small></li>)}</ul>}
    </section>
    {status&&<p role="status">{status}</p>}
  </main>;
}

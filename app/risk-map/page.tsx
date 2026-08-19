'use client';

import {useState} from 'react';

const ENGINE = process.env.NEXT_PUBLIC_ENGINEERING_API || 'http://localhost:8000';

export default function RiskMap() {
  const [findings, setFindings] = useState('[{"id":"wall-1","category":"DFM","message":"Wall thickness below declared process limit","risk_score":0.82}]');
  const [sigma, setSigma] = useState(0.1);
  const [tolerance, setTolerance] = useState(0.4);
  const [result, setResult] = useState<any>();
  const [error, setError] = useState('');

  async function run() {
    setError('');
    try {
      const parsed = JSON.parse(findings);
      if (!Array.isArray(parsed)) throw new Error('Findings must be a JSON array');
      const r = await fetch(`${ENGINE}/v1/risk-map`, {
        method: 'POST',
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({findings: parsed, uncertainty_sigma_mm: sigma, tolerance_mm: tolerance}),
      });
      const body = await r.json();
      if (!r.ok) throw new Error(body.detail || 'Risk map failed');
      setResult(body);
    } catch (e: any) {
      setError(e.message || 'Risk map failed');
    }
  }

  return <main className="page wide">
    <div className="eyebrow">ENGINEERING / RISK MAP</div>
    <h1 className="title">Evidence-backed risk map</h1>
    <p className="muted">Ranks supplied engineering findings and uncertainty. It never turns a risk score into physical acceptance.</p>
    <div className="workspace-grid" style={{marginTop: 24}}>
      <section className="panel">
        <h2>INPUT EVIDENCE</h2>
        <label>Findings JSON<textarea rows={9} value={findings} onChange={e => setFindings(e.target.value)} /></label>
        <label>Uncertainty σ (mm)<input type="number" step="0.001" value={sigma} onChange={e => setSigma(+e.target.value)} /></label>
        <label>Tolerance band (mm)<input type="number" step="0.001" value={tolerance} onChange={e => setTolerance(+e.target.value)} /></label>
        <button className="button primary" onClick={run}>Compute risk map</button>
        {error && <p className="error">{error}</p>}
      </section>
      <section className="panel">
        <h2>RANKED RISKS</h2>
        {result ? <>
          <div className="grid grid3">
            <div className="panel"><strong>{result.summary.critical}</strong><p className="muted">Critical</p></div>
            <div className="panel"><strong>{result.summary.high}</strong><p className="muted">High</p></div>
            <div className="panel"><strong>{result.summary.medium}</strong><p className="muted">Medium</p></div>
          </div>
          {result.risk_map.map((x: any) => <div className="panel" key={x.id}><strong>{x.level.toUpperCase()} · {x.category}</strong><p>{x.message}</p><p className="muted">Risk score: {x.risk_score.toFixed(3)} · Source: {x.source}</p></div>)}
          <pre className="provenance">{JSON.stringify(result.provenance, null, 2)}</pre>
        </> : <p className="muted">No risk map yet.</p>}
      </section>
    </div>
  </main>;
}

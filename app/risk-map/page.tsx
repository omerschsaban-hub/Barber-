'use client';

import {Canvas} from '@react-three/fiber';
import {OrbitControls, Edges} from '@react-three/drei';
import {useState} from 'react';

const ENGINE = process.env.NEXT_PUBLIC_ENGINEERING_API || 'http://localhost:8000';

function RiskMarker({position, score, label}: {position: [number, number, number]; score: number; label: string}) {
  const height = 0.35 + score * 1.15;
  return <group position={position}>
    <mesh position={[0, height / 2, 0]}>
      <cylinderGeometry args={[0.16, 0.16, height, 16]} />
      <meshStandardMaterial color={score >= 0.8 ? '#ef4444' : score >= 0.6 ? '#f59e0b' : '#22c55e'} emissive={score >= 0.8 ? '#7f1d1d' : score >= 0.6 ? '#78350f' : '#14532d'} emissiveIntensity={0.25} />
    </mesh>
    <mesh position={[0, height + 0.08, 0]}>
      <sphereGeometry args={[0.18, 16, 16]} />
      <meshStandardMaterial color={score >= 0.8 ? '#ef4444' : score >= 0.6 ? '#f59e0b' : '#22c55e'} emissive={score >= 0.8 ? '#7f1d1d' : score >= 0.6 ? '#78350f' : '#14532d'} emissiveIntensity={0.4} />
    </mesh>
  </group>;
}

function DemoGeometry() {
  return <>
    <ambientLight intensity={1.3} />
    <directionalLight position={[5, 7, 8]} intensity={2} />
    <group rotation={[0.08, -0.25, 0]}>
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[6.4, 2.2, 4.1]} />
        <meshStandardMaterial transparent opacity={0.12} roughness={0.7} />
        <Edges linewidth={1.5} />
      </mesh>
      <mesh position={[0, -0.72, 0]}>
        <boxGeometry args={[5.9, 0.35, 3.6]} />
        <meshStandardMaterial roughness={0.55} />
        <Edges linewidth={1} />
      </mesh>
      <mesh position={[0, -0.5, 0]}>
        <boxGeometry args={[4.6, 0.28, 2.5]} />
        <meshStandardMaterial roughness={0.45} />
        <Edges linewidth={1} />
      </mesh>
      <RiskMarker position={[-2.75, -0.55, -1.55]} score={0.82} label="Wall thickness" />
      <RiskMarker position={[2.65, -0.55, -1.45]} score={0.67} label="Corner" />
      <RiskMarker position={[0, -0.48, 1.15]} score={0.43} label="Base" />
    </group>
    <gridHelper args={[12, 12, '#334155', '#1e293b']} position={[0, -1.05, 0]} />
    <OrbitControls enableDamping makeDefault />
  </>;
}

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
    <p className="muted">Ranks supplied engineering findings and uncertainty. The 3D view is a visual aid; it never turns a risk score into physical acceptance.</p>

    <section className="panel" style={{marginTop: 24, padding: 0, overflow: 'hidden'}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '18px 20px', borderBottom: '1px solid var(--border)'}}>
        <div><strong>3D GEOMETRY + RISK OVERLAY</strong><p className="muted" style={{margin: '4px 0 0'}}>Demo enclosure preview — drag to orbit, scroll to zoom.</p></div>
        <span className="eyebrow">STEP CONTEXT</span>
      </div>
      <div style={{height: 430, background: '#020617'}}>
        <Canvas camera={{position: [7.5, 5.5, 7.5], fov: 42}}>
          <DemoGeometry />
        </Canvas>
      </div>
      <div style={{display: 'flex', gap: 18, padding: '12px 20px', flexWrap: 'wrap'}} className="muted">
        <span>● High risk</span><span>● Medium risk</span><span>● Lower risk</span><span>3D shape is visualized from the same declared demo dimensions as the supplied STEP fixture.</span>
      </div>
    </section>

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

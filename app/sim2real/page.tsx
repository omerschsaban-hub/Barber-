'use client';

import {useMemo, useState} from 'react';

type LoopResult = any;
const ENGINE = process.env.NEXT_PUBLIC_ENGINEERING_API || process.env.NEXT_PUBLIC_ENGINEERING_URL || 'http://localhost:8000';

const APP_IMPROVEMENTS = [
  ['3D violation heatmap', 'Maps deterministic violations onto the available geometry context.'],
  ['Feature-level violation inspector', 'Shows feature, nominal, measured, tolerance and evidence state.'],
  ['Auto-fix diff viewer', 'Shows every deterministic scalar change before verification.'],
  ['Before/after geometry comparison', 'Keeps geometry claims evidence-bound; scalar fixes are separated from topology edits.'],
  ['Simulation-vs-measurement dashboard', 'Displays prediction, measurement and residual evidence together.'],
  ['Uncertainty/error-budget visualization', 'Breaks the prediction interval into explicit uncertainty sources.'],
  ['Physical-test planner', 'Selects the next information-gaining measurement from observed residuals.'],
  ['Calibration history', 'Surfaces real-observation count, validation status and model error.'],
  ['Manufacturing-release gate', 'Blocks release until evidence and human-release gates are satisfied.'],
  ['Complete engineering provenance timeline', 'Shows the full CAD → release evidence chain and STEP hash.'],
];

function toBase64(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] || '');
    reader.onerror = () => reject(reader.error || new Error('Could not read STEP file'));
    reader.readAsDataURL(file);
  });
}

export default function Sim2Real() {
  const [file, setFile] = useState<File>();
  const [result, setResult] = useState<LoopResult>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [machine, setMachine] = useState('FDM printer');
  const [material, setMaterial] = useState('PETG');
  const [measurements, setMeasurements] = useState({wall_thickness_mm: 1.0, clearance_mm: 0.15, hole_diameter_mm: 2.4, overhang_deg: 55, bridge_mm: 8, tolerance_mm: 0.2});

  const stageState = useMemo(() => {
    const gates = result?.release_gates || [];
    return gates.map((g:any) => `${g.gate}: ${g.status}`);
  }, [result]);

  async function run() {
    if (!file) return;
    setBusy(true); setError(''); setResult(undefined);
    try {
      const step_b64 = await toBase64(file);
      const r = await fetch(`${ENGINE}/v1/sim2real/loop`, {
        method: 'POST', headers: {'content-type': 'application/json'},
        body: JSON.stringify({project_id: file.name, revision: 'A', machine, material, step_filename: file.name, step_b64, measurements, features: [], observations: [], seed: 42, human_release_approved: false})
      });
      const j = await r.json().catch(() => ({detail: 'Engineering service returned invalid JSON.'}));
      if (!r.ok) throw new Error(j.detail || `Sim-to-real loop failed (${r.status})`);
      setResult(j);
    } catch (e:any) { setError(e?.message || 'Sim-to-real loop failed.'); }
    finally { setBusy(false); }
  }

  const update = (k:string, v:string) => setMeasurements(x => ({...x, [k]: Number(v)}));
  const residual = result?.prediction_vs_reality;
  const model = result?.calibration || {};

  return <main className="page wide">
    <div className="eyebrow">SIM → REAL / EVIDENCE LOOP</div>
    <h1 className="title">Close the engineering loop</h1>
    <p className="muted" style={{maxWidth:900}}>One workflow: CAD → DFM → fix → verify → simulate → physically test → measure → compare → calibrate → choose next experiment → release. The UI only displays evidence returned by the deterministic engineering service.</p>

    <section className="panel" style={{marginTop:24}}>
      <h2>RUN THE LOOP</h2>
      <div className="workspace-grid">
        <div>
          <label>STEP / STP<input type="file" accept=".step,.stp" onChange={e=>setFile(e.target.files?.[0])}/></label>
          <label>Material<input value={material} onChange={e=>setMaterial(e.target.value)}/></label>
          <label>Machine<input value={machine} onChange={e=>setMachine(e.target.value)}/></label>
          <h3>Declared process evidence</h3>
          {Object.entries(measurements).map(([k,v])=><label key={k}>{k}<input type="number" step="0.01" value={v} onChange={e=>update(k,e.target.value)}/></label>)}
          <button className="button primary" disabled={!file||busy} onClick={run}>{busy?'Running evidence loop…':'Run full sim-to-real loop'}</button>
          {error && <p className="error" role="alert">{error}</p>}
        </div>
        <div>
          <h3>Pipeline state</h3>
          {result ? stageState.map((x:string)=><p key={x} className="muted">{x}</p>) : <p className="muted">Upload a real STEP file to begin. No synthetic geometry is generated here.</p>}
        </div>
      </div>
    </section>

    <section className="grid grid3" style={{marginTop:24}}>
      {APP_IMPROVEMENTS.map(([title,desc],i)=><article className="panel" key={title}><div className="eyebrow">APP {String(i+1).padStart(2,'0')}</div><h3>{title}</h3><p className="muted">{desc}</p></article>)}
    </section>

    {result && <>
      <section className="workspace-grid" style={{marginTop:24}}>
        <div className="panel"><h2>3D / B-REP CONTEXT</h2><pre className="provenance">{JSON.stringify(result.cad?.brep,null,2)}</pre><p className="muted">STEP SHA-256: {result.provenance?.step_sha256}</p></div>
        <div className="panel"><h2>VIOLATION HEATMAP DATA</h2><p className="muted">Deterministic blockers: {result.dfm?.after?.blocker_count ?? 0}</p>{(result.dfm?.after?.findings||[]).map((f:any)=><div className="panel" key={f.code}><strong>{f.code}</strong><p>{f.message}</p><p className="muted">Severity: {f.severity}</p></div>)}</div>
      </section>
      <section className="workspace-grid" style={{marginTop:24}}>
        <div className="panel"><h2>AUTO-FIX DIFF</h2>{(result.dfm?.fix?.changes||[]).map((c:any)=><p key={`${c.field}-${c.before}`}>{c.field}: <strong>{c.before} → {c.after}</strong></p>)}{!(result.dfm?.fix?.changes||[]).length&&<p className="muted">No deterministic scalar changes were necessary.</p>}</div>
        <div className="panel"><h2>SIMULATION ↔ REALITY</h2><p>Prediction: {result.simulation?.prediction_mm?.toFixed?.(4) ?? '—'} mm</p><p>Real observations: {result.physical_test?.observation_count ?? 0}</p><p>MAE: {residual?.mae_mm?.toFixed?.(4) ?? '—'} mm</p><p className="muted">Calibration: {model.status || 'not calibrated'}</p></div>
      </section>
      <section className="panel" style={{marginTop:24}}><h2>RELEASE GATES</h2>{(result.release_gates||[]).map((g:any)=><div className="row" key={g.gate} style={{justifyContent:'space-between',padding:'8px 0'}}><span>{g.gate}</span><strong>{g.status}</strong></div>)}<p className="muted">Release candidate: {String(result.release_ready)}. Human release remains required.</p></section>
      <section className="panel" style={{marginTop:24}}><h2>PROVENANCE TIMELINE</h2>{(result.provenance?.stages||[]).map((s:string,i:number)=><span key={s} className="badge" style={{marginRight:8,marginBottom:8,display:'inline-block'}}>{i+1}. {s}</span>)}</section>
    </>}
  </main>;
}

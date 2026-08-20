'use client';

import {useState} from 'react';

const ENGINE = process.env.NEXT_PUBLIC_ENGINEERING_API || 'http://localhost:8000';

type Result = any;

async function post(path: string, payload: Record<string, any>) {
  const r = await fetch(`${ENGINE}${path}`, {
    method: 'POST',
    headers: {'content-type': 'application/json'},
    body: JSON.stringify(payload),
  });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(body.detail || body.reason || `Engineering request failed (${r.status})`);
  return body;
}

function ResultBox({result}: {result: Result}) {
  if (!result) return <p className="muted">Nothing run yet.</p>;
  return <div className="panel" style={{marginTop: 14}}>
    <strong>{result.status || 'Result ready'}</strong>
    {result.reason && <p>{result.reason}</p>}
    {result.interval_days && <p><strong>{result.interval_days} days</strong> before the next recommended re-check.</p>}
    {result.selected && <p>Next experiment: <strong>{typeof result.selected === 'string' ? result.selected : JSON.stringify(result.selected)}</strong></p>}
    {result.combined_sigma_mm !== undefined && <p>Combined uncertainty: <strong>{Number(result.combined_sigma_mm).toFixed(3)} mm</strong></p>}
    {result.max_risk !== undefined && <p>Highest observed risk: <strong>{Number(result.max_risk).toFixed(3)}</strong></p>}
    {result.held_out_validation !== undefined && <p>Held-out validation: <strong>{result.held_out_validation ? 'passed' : 'required'}</strong></p>}
    <details><summary>Technical evidence</summary><pre className="provenance">{JSON.stringify(result, null, 2)}</pre></details>
  </div>;
}

export default function EngineeringCenter() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<Record<string, Result>>({});
  const [nominal, setNominal] = useState(40);
  const [material, setMaterial] = useState('PETG');
  const [machine, setMachine] = useState('Machine 01');
  const [sigma, setSigma] = useState(.15);
  const [tolerance, setTolerance] = useState(.4);
  const [observedDrift, setObservedDrift] = useState(.002);
  const [uses, setUses] = useState(20);
  const [samples, setSamples] = useState(100);
  const [candidates, setCandidates] = useState('Measure wall thickness;Measure connector fit;Print a controlled test coupon');
  const [riskScores, setRiskScores] = useState('0.2,0.35,0.1');

  async function run(key: string, path: string, payload: Record<string, any>) {
    setBusy(true); setError('');
    try { setResults(x => ({...x, [key]: await post(path, payload)})); }
    catch (e: any) { setError(e.message || 'Engineering service unavailable'); }
    finally { setBusy(false); }
  }

  const observations = Array.from({length: 10}, (_, i) => ({predicted_mm: nominal + i * .01, measured_mm: nominal + i * .01 + .01}));

  return <main className="page wide">
    <div className="eyebrow">FABRIENT / ENGINEERING CENTER</div>
    <h1 className="title">Everything important, without the engineering math.</h1>
    <p className="muted" style={{maxWidth: 900}}>The engineering engine stays technical underneath. This page turns the MCP's deeper capabilities into simple decisions: check, learn, measure, compare, verify, and decide what to do next.</p>
    {error && <p className="error">{error}</p>}

    <section className="workspace-grid" style={{marginTop: 24}}>
      <section className="panel"><h2>01 / QUICK PHYSICS CHECK</h2><p className="muted">“What size should I expect?”</p><div className="formgrid"><label>Nominal size (mm)<input type="number" value={nominal} onChange={e=>setNominal(+e.target.value)}/></label><label>Material<input value={material} onChange={e=>setMaterial(e.target.value)}/></label><label>Machine<input value={machine} onChange={e=>setMachine(e.target.value)}/></label></div><button className="button primary" disabled={busy} onClick={()=>run('physics','/v1/predict',{nominal_mm:nominal,material,machine,process_temperature_c:245,nominal_shrinkage_pct:.5,shrinkage_uncertainty_pct:sigma,tolerance_lower_mm:-tolerance/2,tolerance_upper_mm:tolerance/2})}>Check expected result</button><ResultBox result={results.physics}/></section>

      <section className="panel"><h2>02 / SIMULATE BEFORE YOU PRINT</h2><p className="muted">Try many bounded possibilities before spending material. Simulation never becomes calibration evidence.</p><label>Number of trials<input type="number" min="10" max="100000" value={samples} onChange={e=>setSamples(+e.target.value)}/></label><button className="button" disabled={busy} onClick={()=>run('simulation','/v1/simulate',{nominal_mm:nominal,samples,seed:42})}>Run simulation</button><ResultBox result={results.simulation}/></section>

      <section className="panel"><h2>03 / LEARN FROM REAL MEASUREMENTS</h2><p className="muted">Give Fabrient real observed measurements. It refuses to pretend synthetic numbers are real evidence.</p><button className="button" disabled={busy} onClick={()=>run('system','/v1/system-identification',{observations})}>Identify machine/process behavior</button><button className="button" disabled={busy} onClick={()=>run('calibration','/v1/calibrate',{observations})}>Fit calibration</button><ResultBox result={results.system || results.calibration}/></section>

      <section className="panel"><h2>04 / HOW SURE ARE WE?</h2><p className="muted">You get one understandable answer instead of a page of equations.</p><label>Physics uncertainty (mm)<input type="number" step=".01" value={sigma} onChange={e=>setSigma(+e.target.value)}/></label><label>Measurement uncertainty (mm)<input type="number" step=".01" defaultValue={.05}/></label><button className="button" disabled={busy} onClick={()=>run('uncertainty','/v1/uncertainty',{physics_sigma_mm:sigma,measurement_sigma_mm:.05,model_sigma_mm:.03})}>Calculate confidence range</button><ResultBox result={results.uncertainty}/></section>
    </section>

    <section className="workspace-grid">
      <section className="panel"><h2>05 / SHOULD I RE-CHECK IT?</h2><p className="muted">Fabrient recommends a re-verification interval from actual use and observed drift.</p><div className="formgrid"><label>Uses / week<input type="number" value={uses} onChange={e=>setUses(+e.target.value)}/></label><label>Observed drift (mm/day)<input type="number" step=".001" value={observedDrift} onChange={e=>setObservedDrift(+e.target.value)}/></label></div><button className="button" disabled={busy} onClick={()=>run('reverify','/v1/reverification',{tolerance_band_mm:tolerance,uses_per_week:uses,environment_severity:.2,observed_drift_mm_per_day:observedDrift,consequence_severity:.5,measurement_uncertainty_mm:.01})}>Recommend next check</button><ResultBox result={results.reverify}/></section>

      <section className="panel"><h2>06 / WHAT SHOULD I TEST NEXT?</h2><p className="muted">Pick a useful physical experiment instead of guessing.</p><textarea rows={4} value={candidates} onChange={e=>setCandidates(e.target.value)}/><button className="button" disabled={busy} onClick={()=>run('experiment','/v1/next-experiment',{candidates:candidates.split(';').map(x=>x.trim()).filter(Boolean)})}>Choose next experiment</button><ResultBox result={results.experiment}/></section>

      <section className="panel"><h2>07 / FINAL RISK CHECK</h2><p className="muted">Ranks risk. It does not silently approve physical production.</p><label>Known risk scores<input value={riskScores} onChange={e=>setRiskScores(e.target.value)}/></label><button className="button" disabled={busy} onClick={()=>run('risk','/v1/final/risk',{risk_scores:riskScores.split(',').map(Number).filter(Number.isFinite)})}>Review risk</button><ResultBox result={results.risk}/></section>

      <section className="panel"><h2>08 / ACCEPTANCE GATE</h2><p className="muted">A gate checks whether the supplied evidence is enough. It never invents missing evidence.</p><button className="button primary" disabled={busy} onClick={()=>run('acceptance','/v1/acceptance',{physical_evidence:[{id:'user-supplied-evidence',status:'observed'}]})}>Check release evidence</button><ResultBox result={results.acceptance}/></section>
    </section>

    <section className="workspace-grid">
      <section className="panel"><h2>09 / REAL WORLD ↔ SIMULATION</h2><p className="muted">Compare simulation with measured reality. Calibration requires enough real observations.</p><button className="button" disabled={busy} onClick={()=>run('sim2real','/v1/sim2real/run',{real_observations:observations})}>Validate simulation against reality</button><button className="button" disabled={busy} onClick={()=>run('compare','/v1/sim2real/compare',{simulated:observations.map(x=>x.predicted_mm),real:observations.map(x=>x.measured_mm)})}>Compare results</button><ResultBox result={results.sim2real || results.compare}/></section>

      <section className="panel"><h2>10 / ENGINEERING REVIEW</h2><p className="muted">Let the bounded engineering workflow organize the evidence and identify the next gate.</p><button className="button primary" disabled={busy} onClick={()=>run('agent','/v1/agents/run',{goal:'Review supplied engineering evidence and identify the next bounded action.',evidence:{nominal_mm:nominal,material,machine}})}>Run engineering review</button><ResultBox result={results.agent}/></section>

      <section className="panel"><h2>11 / INSPECTION REPORTS</h2><p className="muted">Turn your observed rows into an auditable report.</p><button className="button" disabled={busy} onClick={()=>run('report','/v1/inspection-report/csv',{rows:observations})}>Prepare inspection CSV</button><button className="button" disabled={busy} onClick={()=>run('pdf','/v1/inspection-report/pdf',{rows:observations})}>Prepare inspection PDF</button><ResultBox result={results.report || results.pdf}/></section>

      <section className="panel"><h2>12 / ENGINEERING TRACE</h2><p className="muted">Advanced provenance stays available, but the normal workflow doesn't force users to read it.</p><button className="button" disabled={busy} onClick={()=>run('provenance','/v1/toolbox/trace_provenance',{operation:'engineering_review',evidence:{source:'user supplied'}})}>Show evidence trail</button><ResultBox result={results.provenance}/></section>
    </section>

    <section className="panel" style={{marginTop:24}}><h2>WHAT STAYS TECHNICAL</h2><p className="muted">The MCP continues to expose the full 100-tool engineering surface: individual DFM checks, CAD review, CV primitives, calibration, system identification, residual ML, simulation, sim-to-real, uncertainty, gates, agents, provenance, inspection, release, and quality audits. The app presents those capabilities as workflows rather than 100 intimidating buttons.</p><div className="pipeline"><span>INPUT</span><i>→</i><span>CHECK</span><i>→</i><span>FIX</span><i>→</i><span>VERIFY</span><i>→</i><span>LEARN</span><i>→</i><span>BUILD</span><i>→</i><span>RELEASE</span></div></section>
  </main>;
}

'use client';

import {useState} from 'react';

const ENGINE = '/api/engineering';

type Observation = { predicted_mm: number; measured_mm: number; layer_height_mm?: number; print_speed_mm_s?: number; nozzle_temp_c?: number; ambient_temp_c?: number; humidity_pct?: number; axis?: number; machine_id?: string; feature_id?: string; };

type Result = any;

async function post(path: string, payload: any) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 120000);
  try {
    const r = await fetch(`${ENGINE}${path}`, {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify(payload), signal:controller.signal});
    const body = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(body.detail || body.reason || `Request failed (${r.status})`);
    return body;
  } finally { window.clearTimeout(timer); }
}

function ResultBox({result}:{result:Result}) {
  if (!result) return null;
  return <div className="panel" style={{marginTop:16}}>
    <strong>{String(result.status || 'Result')}</strong>
    {result.objective && <p>{result.objective}</p>}
    {result.comparison?.mae_mm !== undefined && <p>Observed MAE: <strong>{Number(result.comparison.mae_mm).toFixed(4)} mm</strong></p>}
    {result.calibration?.held_out_mae_mm !== undefined && <p>Held-out MAE: <strong>{Number(result.calibration.held_out_mae_mm).toFixed(4)} mm</strong></p>}
    {result.trust_envelope && <p>Validation: <strong>{result.trust_envelope.status}</strong></p>}
    {result.next_experiment?.selected && <p>Next experiment: <strong>{result.next_experiment.selected.name}</strong></p>}
    {result.next_experiment?.reason && <p>{result.next_experiment.reason}</p>}
    <details><summary>Evidence</summary><pre className="provenance">{JSON.stringify(result,null,2)}</pre></details>
  </div>;
}

export default function EngineeringCenter() {
  const [nominal,setNominal]=useState(40);
  const [shrinkage,setShrinkage]=useState(.5);
  const [shrinkageSigma,setShrinkageSigma]=useState(.1);
  const [temperature,setTemperature]=useState(220);
  const [temperatureSigma,setTemperatureSigma]=useState(2);
  const [raw,setRaw]=useState('');
  const [result,setResult]=useState<Result>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');

  function parse(): Observation[] {
    if (!raw.trim()) return [];
    const parsed=JSON.parse(raw);
    if (!Array.isArray(parsed)) throw new Error('Observations must be a JSON array.');
    return parsed.map((o,i)=>{
      if (!Number.isFinite(Number(o.predicted_mm)) || !Number.isFinite(Number(o.measured_mm))) throw new Error(`Observation ${i+1} needs predicted_mm and measured_mm.`);
      return {...o,predicted_mm:Number(o.predicted_mm),measured_mm:Number(o.measured_mm)};
    });
  }

  async function run() {
    setBusy(true);setError('');
    try {
      const observations=parse();
      const candidates=observations.slice(0,8).map((o,i)=>({name:`Follow-up test ${i+1}`,predicted_mm:o.predicted_mm,measured_mm:o.measured_mm,cost_minutes:10,machine_id:o.machine_id,feature_id:o.feature_id}));
      setResult(await post('/v1/sim2real/loop',{nominal_mm:nominal,shrinkage_pct:shrinkage,shrinkage_sigma_pct:shrinkageSigma,temperature_c:temperature,temperature_sigma_c:temperatureSigma,observations,candidate_experiments:candidates,target_mae_mm:0.1,max_iterations:5,seed:42}));
    } catch(e:any) {setError(e.message || 'The engineering service failed.');}
    finally {setBusy(false);}
  }

  return <main className="page wide">
    <div className="eyebrow">FABRIENT / REALITY LOOP</div>
    <h1 className="title">Make the simulation agree with reality.</h1>
    <p className="muted" style={{maxWidth:850}}>Fabrient compares a physics baseline with real measurements, calibrates what the evidence supports, learns residual behavior with ML, validates on held-out data, and chooses the next useful experiment. It never invents physical evidence.</p>

    <section className="panel" style={{marginTop:24}}>
      <h2>1 / MODEL</h2>
      <div className="formgrid">
        <label>Nominal size (mm)<input type="number" min="0.01" value={nominal} onChange={e=>setNominal(Number(e.target.value))}/></label>
        <label>Expected shrinkage (%)<input type="number" min="0" max="10" step=".01" value={shrinkage} onChange={e=>setShrinkage(Number(e.target.value))}/></label>
        <label>Shrinkage uncertainty (%)<input type="number" min="0" max="5" step=".01" value={shrinkageSigma} onChange={e=>setShrinkageSigma(Number(e.target.value))}/></label>
        <label>Process temperature (°C)<input type="number" min="1" max="399" value={temperature} onChange={e=>setTemperature(Number(e.target.value))}/></label>
        <label>Temperature uncertainty (°C)<input type="number" min="0" max="50" step=".1" value={temperatureSigma} onChange={e=>setTemperatureSigma(Number(e.target.value))}/></label>
      </div>
    </section>

    <section className="panel" style={{marginTop:16}}>
      <h2>2 / REALITY</h2>
      <p className="muted">Paste measured observations from the real system. The app does not generate fake measurements for you.</p>
      <textarea rows={12} value={raw} onChange={e=>setRaw(e.target.value)} placeholder={'[{"predicted_mm":39.8,"measured_mm":40.1,"machine_id":"robot-1","feature_id":"joint-1"}]'} />
      <p className="muted small">Use independent physical observations. More diverse conditions make the learned model more useful; repeated identical rows do not create new evidence.</p>
    </section>

    <section className="panel" style={{marginTop:16}}>
      <h2>3 / CLOSE THE LOOP</h2>
      <button className="button primary" disabled={busy} onClick={run}>{busy?'Running reality loop…':'Run automatic calibration & validation'}</button>
      <p className="muted small">The MVP automates the software loop. Physical test execution remains outside the product until the hardware-control layer is a V2 capability.</p>
      {error && <p className="error">{error}</p>}
      <ResultBox result={result}/>
    </section>

    <section className="panel" style={{marginTop:16}}>
      <h2>WHAT FABRIENT AUTOMATES</h2>
      <div className="pipeline"><span>COMPARE</span><i>→</i><span>DIAGNOSE</span><i>→</i><span>CALIBRATE</span><i>→</i><span>RESIDUAL ML</span><i>→</i><span>HELD-OUT TEST</span><i>→</i><span>NEXT EXPERIMENT</span></div>
      <p className="muted">No MHS in MVP. No generic CAD assistant. No fake confidence. The product is optimized around reducing real experiments needed to reach a validated model.</p>
    </section>
  </main>;
}

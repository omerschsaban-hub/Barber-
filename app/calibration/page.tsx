'use client';
import {useState} from 'react';

const ENGINE = '/api/engineering';

export default function Calibration(){
  const [nom,setNom]=useState(40); const [shrink,setShrink]=useState(.5); const [unc,setUnc]=useState(.15);
  const [result,setResult]=useState<any>(); const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  async function run(){
    setBusy(true); setError(''); setResult(undefined);
    try {
      const r=await fetch(`${ENGINE}/v1/predict`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({nominal_mm:nom,material:'PETG',machine:'unspecified',process_temperature_c:245,ambient_temperature_c:23,nominal_shrinkage_pct:shrink,shrinkage_uncertainty_pct:unc,tolerance_lower_mm:-.2,tolerance_upper_mm:.2})});
      const j=await r.json().catch(()=>({detail:'Engineering service returned invalid JSON.'}));
      if(!r.ok) throw new Error(j.detail||`Engineering request failed (${r.status})`);
      if(typeof j.prediction_mm!=='number'||!Array.isArray(j.interval_95_mm)) throw new Error('Engineering response is missing the prediction interval.');
      setResult(j);
    } catch(e:any){ setError(e?.message||'Unable to run the deterministic baseline.'); }
    finally{setBusy(false)}
  }
  return <main className="page"><div className="eyebrow">SIM-TO-REAL / BASELINE</div><h1 className="title">Physics first. Measurements decide.</h1><div className="grid grid2"><div className="panel"><div className="field"><label>Nominal dimension (mm)</label><input type="number" min="0" step=".01" value={nom} onChange={e=>setNom(+e.target.value)}/></div><div className="field"><label>Assumed shrinkage (%)</label><input type="number" step=".01" value={shrink} onChange={e=>setShrink(+e.target.value)}/></div><div className="field"><label>Shrinkage uncertainty (%)</label><input type="number" min="0" step=".01" value={unc} onChange={e=>setUnc(+e.target.value)}/></div><button className="button" disabled={busy||nom<=0||unc<0} onClick={run}>{busy?'Running…':'Run deterministic baseline'}</button>{error&&<p className="error">{error}</p>}</div><div className="panel">{result?<><div className="eyebrow">RESULT / {result.provenance?.version||'deterministic'}</div><div className="metric">{result.prediction_mm.toFixed(3)} mm</div><p className="muted">95% interval: {result.interval_95_mm.map((x:number)=>x.toFixed(3)).join(' — ')} mm</p><span className="status warn">{result.status}</span><p className="annotation">This is a physics baseline, not a claim about your machine. Real measurements are required before calibration.</p></>:<p className="muted">No prediction yet.</p>}</div></div></main>
}

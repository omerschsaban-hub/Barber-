'use client';
import {useState} from 'react';
export default function Experiments(){
  const [result,setResult]=useState<any>(); const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  async function choose(){
    setBusy(true);setError('');setResult(undefined);
    try{
      const r=await fetch('/api/engineering/v1/next-experiment?machine_id=unassigned',{method:'POST',headers:{'content-type':'application/json'},body:'{}',cache:'no-store'});
      const j=await r.json().catch(()=>({detail:'Engineering service returned invalid JSON.'}));
      if(!r.ok) throw new Error(j.detail||j.error||`Engineering request failed (${r.status})`);
      if(!j.experiment||!Array.isArray(j.experiment.dimensions_mm)||!Array.isArray(j.experiment.features)) throw new Error('Experiment response is incomplete.');
      setResult(j);
    }catch(e:any){setError(e?.message||'Unable to select the next experiment.');}
    finally{setBusy(false)}
  }
  return <main className="page"><div className="eyebrow">ACTIVE LEARNING</div><h1 className="title">Choose the next physical experiment.</h1><p className="muted">The experiment engine is intentionally conservative: with no real residual history, it asks for a baseline measurement instead of pretending it knows which parameter matters.</p><div className="panel" style={{marginTop:24}}><button className="button" disabled={busy} onClick={choose}>{busy?'Selecting…':'Select next experiment'}</button>{error&&<p className="error" style={{marginTop:16}}>{error}</p>}{result&&<div style={{marginTop:22}}><span className="status good">{result.experiment.expected_information_gain} information value</span><h2>{result.experiment.type}</h2><p>Print: {result.experiment.dimensions_mm.join(' × ')} mm</p><p className="muted">Features: {result.experiment.features.join(', ')}</p><p className="annotation">{result.experiment.reason}</p></div>}</div></main>
}
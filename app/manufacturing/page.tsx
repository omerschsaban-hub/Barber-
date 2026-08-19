'use client';
import {useState} from 'react';

const ENGINE=process.env.NEXT_PUBLIC_ENGINEERING_API||'http://localhost:8000';

type Result=any;

export default function Manufacturing(){
  const [part,setPart]=useState('Electronics enclosure');
  const [revision,setRevision]=useState('A');
  const [material,setMaterial]=useState('PETG');
  const [machine,setMachine]=useState('FDM printer');
  const [measurements,setMeasurements]=useState({wall_thickness_mm:1.0,clearance_mm:0.15,hole_diameter_mm:2.4,overhang_deg:55,bridge_mm:8,tolerance_mm:0.2});
  const [result,setResult]=useState<Result>();
  const [pkg,setPkg]=useState<Result>();
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const update=(k:string,v:string)=>setMeasurements(x=>({...x,[k]:Number(v)}));
  async function post(path:string,body:any){const r=await fetch(`${ENGINE}${path}`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Engineering request failed');return j;}
  async function analyze(){setBusy(true);setError('');try{setResult(await post('/v1/dfm/analyze',{part_name:part,revision,material,machine,measurements}));}catch(e:any){setError(e.message)}finally{setBusy(false)}}
  async function selfFix(){setBusy(true);setError('');try{setResult(await post('/v1/dfm/self-fix',{part_name:part,revision,material,machine,measurements}));}catch(e:any){setError(e.message)}finally{setBusy(false)}}
  async function packageIt(){setBusy(true);setError('');try{setPkg(await post('/v1/manufacturing/package',{project_name:part,revision,material,machine,dfm_result:result?.after||result}));}catch(e:any){setError(e.message)}finally{setBusy(false)}}
  return <main className="page wide">
    <div className="eyebrow">MANUFACTURING / RELEASE</div>
    <h1 className="title">Fix it. Verify it. Package it.</h1>
    <p className="muted" style={{maxWidth:820}}>Fabrient checks declared manufacturing constraints, applies only deterministic scalar fixes, shows exactly what changed, re-runs the checks, and builds a release-candidate manufacturing package. Geometry/topology edits remain explicitly human-gated.</p>
    <div className="workspace-grid" style={{marginTop:28}}>
      <section className="panel">
        <h2>PART INPUT</h2>
        <label>Part name<input value={part} onChange={e=>setPart(e.target.value)}/></label>
        <label>Revision<input value={revision} onChange={e=>setRevision(e.target.value)}/></label>
        <label>Material<input value={material} onChange={e=>setMaterial(e.target.value)}/></label>
        <label>Machine<input value={machine} onChange={e=>setMachine(e.target.value)}/></label>
        <h3 style={{marginTop:20}}>Declared dimensions / process limits</h3>
        {Object.entries(measurements).map(([k,v])=><label key={k}>{k}<input type="number" step="0.01" value={v} onChange={e=>update(k,e.target.value)}/></label>)}
        <div className="row" style={{marginTop:16}}><button className="button" disabled={busy} onClick={analyze}>Analyze</button><button className="button primary" disabled={busy} onClick={selfFix}>Self-fix + verify</button></div>
        {error&&<p className="error">{error}</p>}
      </section>
      <section className="panel">
        <h2>WHAT FABRIENT FIXED</h2>
        {!result&&<p className="muted">Run the self-fix pass to see before → after changes and remaining blockers.</p>}
        {result?.changes?.length>0&&<div>{result.changes.map((c:any,i:number)=><div className="panel" key={i}><strong>{c.issue}</strong><p className="muted">{c.field}: {c.before} → {c.after}</p><p>{c.reason}</p></div>)}</div>}
        {result?.changes?.length===0&&result&&<p>No deterministic scalar changes were necessary.</p>}
        {result?.refused?.length>0&&<><h3>Human/CAD fixes required</h3>{result.refused.map((x:any,i:number)=><p className="muted" key={i}>• {x.finding?.code}: {x.reason}</p>)}</>}
        {result?.after&&<div className="panel"><strong>Verification: {result.after.status}</strong><p>{result.after.blocker_count} blocker(s) remain.</p></div>}
      </section>
    </div>
    <section className="panel" style={{marginTop:24}}>
      <div className="row" style={{justifyContent:'space-between'}}><div><h2>MANUFACTURING PACKAGE</h2><p className="muted">Generate only after reviewing the DFM result.</p></div><button className="button primary" disabled={!result||busy} onClick={packageIt}>Generate package</button></div>
      {pkg&&<div style={{marginTop:18}}><div className="grid grid3">{pkg.contents?.map((x:any)=><div className="panel" key={x.name}><strong>{x.name}</strong><p className="muted">{x.type}</p></div>)}</div><pre className="provenance">{JSON.stringify(pkg.gates,null,2)}</pre><p className="muted">Manifest SHA-256: {pkg.manifest_sha256}</p></div>}
    </section>
  </main>
}

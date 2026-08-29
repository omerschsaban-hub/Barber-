'use client';
import Link from 'next/link';
import {useEffect, useMemo, useState} from 'react';
import {EngineeringProfile, ENGINEERING_PROFILE_DEFAULTS, loadEngineeringProfile, saveEngineeringProfile} from '@/lib/engineering-profile';

const ENGINE = '/api/engineering';

type Profile = EngineeringProfile;

export default function Calibration() {
  const [profile,setProfile]=useState<Profile>(ENGINEERING_PROFILE_DEFAULTS);
  const [advanced,setAdvanced]=useState(false);
  const [result,setResult]=useState<any>();
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [saved,setSaved]=useState(false);
  const [hasRealProfile,setHasRealProfile]=useState(false);

  useEffect(() => {
    const stored=loadEngineeringProfile();
    if(stored){setProfile(stored);setSaved(true);setHasRealProfile(true);}
  },[]);

  function set<K extends keyof Profile>(key:K,value:Profile[K]) {
    setProfile(current=>{
      const next={...current,[key]:value};
      setSaved(saveEngineeringProfile(next));
      return next;
    });
    setHasRealProfile(true);
  }

  async function run() {
    setBusy(true);setError('');setResult(undefined);
    try {
      const p=profile;
      const r=await fetch(`${ENGINE}/v1/predict`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({nominal_mm:p.nominal_mm,material:p.material,machine:p.machine,process_temperature_c:p.process_temperature_c,ambient_temperature_c:p.ambient_temperature_c,nominal_shrinkage_pct:p.shrinkage_pct,shrinkage_uncertainty_pct:p.shrinkage_uncertainty_pct,tolerance_lower_mm:-p.tolerance_mm/2,tolerance_upper_mm:p.tolerance_mm/2}),signal:AbortSignal.timeout(120_000)});
      const j=await r.json().catch(()=>({detail:'Engineering service returned invalid JSON.'}));
      if(!r.ok)throw new Error(j.detail||`Engineering request failed (${r.status})`);
      if(typeof j.prediction_mm!=='number'||!Array.isArray(j.interval_95_mm))throw new Error('Engineering response is missing the prediction interval.');
      setResult(j);
    } catch(e:any) {setError(e?.name==='TimeoutError'?'The calculation took too long. No result was accepted.':(e?.message||'Unable to run the deterministic baseline.'));}
    finally {setBusy(false);}
  }

  const profileSummary=useMemo(()=>`${profile.material} · ${profile.machine}`,[profile.material,profile.machine]);

  return <main className="page">
    <div className="eyebrow">MONITORING / CALIBRATION</div>
    <div className="workspace-head"><div><h1 className="title">Better accuracy, less typing.</h1><p className="muted">Keep the technical controls when they improve the answer. Fabrient remembers values you actually set, while clearly separating assumptions from real machine measurements.</p></div><span className={`status ${hasRealProfile?'ok':'warn'}`}>{hasRealProfile&&saved?'SAVED PROFILE':'BASELINE ONLY'}</span></div>

    <section className="panel" style={{marginTop:20}}><div className="eyebrow">READY TO RUN</div><h2>{profileSummary}</h2><p className="muted">Run the deterministic baseline now. It is useful for a starting estimate; calibration becomes more accurate when real observations are added.</p><button className="button primary" disabled={busy||profile.nominal_mm<=0||profile.shrinkage_uncertainty_pct<0} onClick={run}>{busy?'Running…':'Run baseline'}</button><button className="button" style={{marginLeft:8}} onClick={()=>setAdvanced(v=>!v)}>{advanced?'Hide technical inputs':'Improve accuracy'}</button><Link className="button" href="/records" style={{marginLeft:8}}>Add real measurements</Link></section>

    {advanced&&<section className="panel" style={{marginTop:14}}><div className="eyebrow">TECHNICAL INPUTS / OPTIONAL</div><p className="muted">These stay available because they can materially improve engineering accuracy. You only need to change them when you have better information.</p><div className="grid grid2"><label className="field">Target dimension (mm)<input type="number" min="0.001" step="0.01" value={profile.nominal_mm} onChange={e=>set('nominal_mm',Number(e.target.value))}/></label><label className="field">Material<input value={profile.material} onChange={e=>set('material',e.target.value)}/></label><label className="field">Machine / printer<input value={profile.machine} onChange={e=>set('machine',e.target.value)}/></label><label className="field">Process temperature (°C)<input type="number" step="1" value={profile.process_temperature_c} onChange={e=>set('process_temperature_c',Number(e.target.value))}/></label><label className="field">Ambient temperature (°C)<input type="number" step="1" value={profile.ambient_temperature_c} onChange={e=>set('ambient_temperature_c',Number(e.target.value))}/></label><label className="field">Expected shrinkage (%)<input type="number" step="0.01" value={profile.shrinkage_pct} onChange={e=>set('shrinkage_pct',Number(e.target.value))}/></label><label className="field">Shrinkage uncertainty (%)<input type="number" min="0" step="0.01" value={profile.shrinkage_uncertainty_pct} onChange={e=>set('shrinkage_uncertainty_pct',Number(e.target.value))}/></label><label className="field">Allowed tolerance (mm)<input type="number" min="0" step="0.01" value={profile.tolerance_mm} onChange={e=>set('tolerance_mm',Number(e.target.value))}/></label></div></section>}

    {error&&<section className="panel" style={{marginTop:14}}><strong>We did not accept the result.</strong><p className="error">{error}</p></section>}
    <section className="panel" style={{marginTop:14}}>{result?<><div className="eyebrow">RESULT / {result.provenance?.version||'deterministic'}</div><div className="metric">{result.prediction_mm.toFixed(3)} mm</div><p className="muted">95% interval: {result.interval_95_mm.map((x:number)=>x.toFixed(3)).join(' — ')} mm</p><span className={`status ${result.status==='pass'?'ok':'warn'}`}>{result.status}</span><p className="annotation">This is a physics baseline, not a measurement of your machine. Real observations remain required before calibration.</p><details><summary>Show assumptions and evidence</summary><pre className="provenance">{JSON.stringify({inputs:profile,result},null,2)}</pre></details></>:<><h2>No baseline yet</h2><p className="muted">Run the baseline, or improve accuracy with real measurements and machine data.</p></>}</section>
  </main>
}

'use client';
import Link from 'next/link';
import {FormEvent, useEffect, useState} from 'react';
import {loadEngineeringProfile} from '@/lib/engineering-profile';

type Result = {status?: string; error?: string; usage?: {message?: string}; intent?: {intent_summary?: string; entity?: string | null; missing_information?: string[]; evidence_sources?: string[]}; engineering?: any};
type SavedProfile = Record<string, unknown>;

const QUICK_ACTIONS = [
  ['Make my design ready to build', 'Check the current design for manufacturability and fix safe issues.'],
  ['Check fit', 'Check fit, clearances, and manufacturability.'],
  ['Find problems', 'Find anything likely to go wrong before I build it.'],
] as const;

export default function EngineeringCopilot() {
  const [input,setInput]=useState('');
  const [busy,setBusy]=useState(false);
  const [result,setResult]=useState<Result|null>(null);
  const [savedProfile,setSavedProfile]=useState<SavedProfile>({});

  useEffect(() => {
    const profile=loadEngineeringProfile();
    if(profile) setSavedProfile(profile);
  }, []);

  async function submit(event?: FormEvent, requested?: string) {
    event?.preventDefault();
    const text=(requested ?? input).trim();
    if(!text || busy)return;
    setBusy(true); setResult(null);
    try {
      const response=await fetch('/api/engineering-intent',{
        method:'POST',
        headers:{'content-type':'application/json'},
        body:JSON.stringify({naturalLanguage:text,execute:true,payload:savedProfile}),
        signal:AbortSignal.timeout(60_000),
      });
      const body=await response.json();
      setResult(response.ok?body:{status:body.status||'Request blocked',error:body.error||'Request failed',usage:body.usage});
    } catch(error:any){
      setResult({status:'failed',error:error?.name==='TimeoutError'?'The request took too long. No engineering result was accepted.':(error?.message||'Request failed')});
    } finally {setBusy(false);}
  }

  const missing=result?.intent?.missing_information||[];
  const nextMissing=missing[0];
  const needsGeometry=Boolean(nextMissing&&/step|stp|cad|geometry|dimension/i.test(nextMissing));
  const hasSavedProfile=Object.keys(savedProfile).length>0;

  return <section className="panel" style={{marginTop:24,border:'1px solid rgba(120,160,255,.35)'}}>
    <div className="eyebrow">ENGINEERING</div>
    <h2 style={{marginBottom:8}}>Start with the job. Fabrient handles the details.</h2>
    <p className="muted">Use a simple goal or bring the real design. Saved engineering context is reused automatically.</p>

    <div className="row" style={{gap:8,flexWrap:'wrap',marginBottom:12}}>
      {QUICK_ACTIONS.map(([label,action])=><button key={action} className="button" type="button" disabled={busy} onClick={()=>{setInput(action);void submit(undefined,action)}}>{label}</button>)}
      <Link className="button" href="/geometry">Add STEP</Link>
      <Link className="button" href="/records">Add measurements</Link>
    </div>

    <form onSubmit={submit} style={{display:'grid',gap:10}}>
      <textarea rows={2} value={input} onChange={e=>setInput(e.target.value.slice(0,12000))} placeholder="What should Fabrient do? (optional if you use a button above)" aria-label="What should Fabrient do"/>
      <button className="button primary" disabled={busy||!input.trim()} type="submit">{busy?'Working…':'Run'}</button>
    </form>

    {hasSavedProfile&&<p className="muted small" style={{marginTop:10}}>Saved machine/material context is reused automatically.</p>}

    {result&&<div className="panel" style={{marginTop:14}}>
      <strong>{result.status||'Result'}</strong>
      {result.intent?.intent_summary&&<p>{result.intent.intent_summary}</p>}
      {result.intent?.entity&&<p><strong>Target:</strong> {result.intent.entity}</p>}
      {nextMissing&&<div>
        <strong>One thing is needed:</strong>
        <p className="muted">{nextMissing}</p>
        {needsGeometry&&<Link className="button" href="/geometry" style={{display:'inline-block',marginTop:8}}>Add STEP file</Link>}
        {!needsGeometry&&<p className="muted small">Provide this once; Fabrient will continue automatically.</p>}
      </div>}
      {result.engineering&&<details style={{marginTop:8}}><summary>Evidence and assumptions</summary><pre className="provenance">{JSON.stringify(result.engineering,null,2)}</pre></details>}
      {result.error&&<p className="error">{result.error}</p>}
      {result.usage?.message&&<p className="muted small">{result.usage.message}</p>}
    </div>}
  </section>;
}

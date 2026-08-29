'use client';
import {FormEvent, useState} from 'react';

type Result = {status?: string; error?: string; usage?: {message?: string}; intent?: {intent_summary?: string; entity?: string | null; missing_information?: string[]}; engineering?: any};
const QUICK_ACTIONS = ['Check my design and make it ready to build.','Check fit and manufacturability.','Find anything that could go wrong before I build it.'];

export default function EngineeringCopilot() {
  const [input,setInput]=useState(''); const [busy,setBusy]=useState(false); const [result,setResult]=useState<Result|null>(null);
  async function submit(event?: FormEvent, requested?: string) {
    event?.preventDefault(); const text=(requested ?? input).trim(); if(!text || busy)return;
    setBusy(true); setResult(null);
    try { const response=await fetch('/api/engineering-intent',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({naturalLanguage:text,execute:true})}); const body=await response.json(); setResult(response.ok?body:{status:body.status||'Request blocked',error:body.error||'Request failed',usage:body.usage}); }
    catch(error:any){setResult({status:'failed',error:error?.message||'Request failed'});} finally{setBusy(false);}
  }
  const missing=result?.intent?.missing_information||[];
  return <section className="panel" style={{marginTop:24,border:'1px solid rgba(120,160,255,.35)'}}>
    <div className="eyebrow">ENGINEERING</div><h2 style={{marginBottom:8}}>Tell Fabrient the outcome. We handle the details.</h2>
    <p className="muted">Bring a STEP file, project, measurements, or just describe the job. Fabrient uses what is already known instead of making you re-enter engineering numbers.</p>
    <div className="row" style={{gap:8,flexWrap:'wrap',marginBottom:12}}>{QUICK_ACTIONS.map(action=><button key={action} className="button" type="button" disabled={busy} onClick={()=>{setInput(action);void submit(undefined,action)}}>{action}</button>)}</div>
    <form onSubmit={submit} style={{display:'grid',gap:10}}><textarea rows={3} value={input} onChange={e=>setInput(e.target.value.slice(0,12000))} placeholder="Or describe the job in plain language…" aria-label="Describe what you want Fabrient to engineer"/><button className="button primary" disabled={busy||!input.trim()} type="submit">{busy?'Working…':'Run with Fabrient'}</button></form>
    {result&&<div className="panel" style={{marginTop:14}}><strong>{result.status||'Result'}</strong>{result.intent?.intent_summary&&<p>{result.intent.intent_summary}</p>}{result.intent?.entity&&<p><strong>Target:</strong> {result.intent.entity}</p>}{missing.length>0&&<div><strong>One thing is needed:</strong><ul>{missing.slice(0,3).map((item,i)=><li key={`${item}-${i}`}>{item}</li>)}</ul></div>}{result.engineering&&<details style={{marginTop:8}}><summary>Engineering evidence</summary><pre className="provenance">{JSON.stringify(result.engineering,null,2)}</pre></details>}{result.error&&<p className="error">{result.error}</p>}{result.usage?.message&&<p className="muted small">{result.usage.message}</p>}</div>}
  </section>;
}

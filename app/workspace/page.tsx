'use client'

import dynamic from 'next/dynamic'
import {useEffect, useMemo, useState} from 'react'

const View3D = dynamic(() => import('@/components/geometry-viewer'), {ssr:false, loading:() => <div className="viewer"><div className="viewer-label">Loading verified 3D view…</div></div>})
const ENGINE='/api/engineering'
const REQUEST_TIMEOUT_MS=120000

type Result=Record<string,any>
const modules=[
  ['intent','Understand','Natural-language engineering intent, entities and constraints'],
  ['cad','Generate CAD','Parametric CAD generation with mandatory STEP round-trip validation'],
  ['analyze','Analyze','Deterministic engineering + ML prediction and uncertainty'],
  ['build','Build','Manufacturing plan, machine/process constraints and release gates'],
  ['inspect','Inspect','Inspection observations, measurements and acceptance decisions'],
  ['calibration','Calibration','Use real observations to improve machine/process models'],
  ['evidence','Evidence','Trace inputs, methods, provenance, validation and decisions'],
  ['exports','Exports','STEP and evidence packages only after release gates pass'],
  ['projects','Projects','Project/revision state and engineering history'],
  ['integrations','Integrations','Connected manufacturing and engineering systems'],
  ['mcp','MCP','Connect the full engineering tool surface to AI clients'],
  ['health','Machine health','Machine state, observations and drift signals']
] as const

async function request(path:string, init:RequestInit={}){
  const controller=new AbortController(); const timer=window.setTimeout(()=>controller.abort(),REQUEST_TIMEOUT_MS)
  try{
    const headers=new Headers(init.headers||{}); if(init.body && !headers.has('content-type')) headers.set('content-type','application/json')
    const r=await fetch(`${ENGINE}${path}`,{...init,headers,signal:controller.signal,cache:'no-store'})
    const text=await r.text(); let body:Result={}; try{body=text?JSON.parse(text):{}}catch{body={detail:text}}
    if(!r.ok) throw new Error(String(body.detail||body.reason||body.error||`Engineering service returned ${r.status}`))
    return body
  }catch(e:any){if(e?.name==='AbortError') throw new Error('The engineering service timed out. No result was accepted.');throw e}
  finally{window.clearTimeout(timer)}
}

function safeJson(value:any){return JSON.stringify(value,null,2).replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g,'')}

export default function Workspace(){
  const [active,setActive]=useState('intent'); const [service,setService]=useState<'checking'|'ready'|'blocked'>('checking'); const [busy,setBusy]=useState(false); const [message,setMessage]=useState('Ready. Nothing runs until you choose an action.')
  const [intent,setIntent]=useState('Create a PETG enclosure for my device with four mounting points and a validated STEP release.')
  const [partName,setPartName]=useState('Fabrient enclosure'); const [revision,setRevision]=useState('A'); const [material,setMaterial]=useState('PETG'); const [width,setWidth]=useState(40); const [depth,setDepth]=useState(30); const [height,setHeight]=useState(20); const [wall,setWall]=useState(2); const [clearance,setClearance]=useState(.25); const [prediction,setPrediction]=useState<Result|null>(null); const [cad,setCad]=useState<Result|null>(null); const [history,setHistory]=useState<string[]>([])

  useEffect(()=>{request('/health').then(()=>setService('ready')).catch(()=>setService('blocked'))},[])
  const statusLabel=service==='checking'?'CONNECTING…':service==='ready'?'ENGINE READY':'ENGINE OFFLINE'; const statusClass=service==='ready'?'ok':'warn'
  const deviation=prediction?Number(prediction.prediction_mm)-40:0

  async function runPrediction(){setBusy(true);setMessage('Running deterministic verification…');try{const r=await request('/v1/predict',{method:'POST',body:JSON.stringify({nominal_mm:40,material,machine:'Machine 01',process_temperature_c:245,nominal_shrinkage_pct:.5,shrinkage_uncertainty_pct:.15,tolerance_lower_mm:-.2,tolerance_upper_mm:.2})});setPrediction(r);setHistory(h=>[`Analyze · ${new Date().toISOString()}`,...h]);setMessage('Verified engineering output received. Review provenance before release.')}catch(e:any){setMessage(e.message)}finally{setBusy(false)}}
  async function generateCad(){setBusy(true);setMessage('Generating parametric CAD and validating the STEP round trip…');try{const r=await request('/v1/geometry/generate',{method:'POST',body:JSON.stringify({width_mm:width,depth_mm:depth,height_mm:height,wall_mm:wall,clearance_mm:clearance,mounting_hole_diameter_mm:2.4,mounting_hole_inset_mm:5,revision,material})});if(r.status!=='validated'||r.format!=='STEP')throw new Error('CAD generation did not produce a validated STEP artifact.');setCad(r);setHistory(h=>[`CAD · ${r.filename}`,...h]);setMessage(`Validated ${r.filename} through the CAD kernel round trip.`)}catch(e:any){setMessage(e.message)}finally{setBusy(false)}}

  const output=useMemo(()=>cad||prediction,[cad,prediction])
  return <main className="page wide">
    <header className="workspace-head"><div><div className="eyebrow">FABRIENT / WORKSPACE</div><h1 className="title">One place to engineer the product.</h1><p className="muted">Describe intent, generate CAD, verify it, build, inspect, learn and release. The old feature pages are no longer separate destinations.</p></div><div className={`status ${statusClass}`} role="status" aria-live="polite">{statusLabel}</div></header>

    <section className="panel" style={{marginTop:16}}><div className="eyebrow">EXECUTION STATUS</div><strong>{message}</strong><p className="muted">Informational screens never execute work. Only explicit actions below can change project state, and rejected/failed results are never presented as accepted.</p></section>

    <section className="panel" style={{marginTop:16}}><div className="eyebrow">ENGINEERING COMMAND</div><label style={{display:'block',marginTop:8}}><span className="muted">Tell Fabrient what you want</span><textarea value={intent} onChange={e=>setIntent(e.target.value)} rows={3} style={{width:'100%',marginTop:6}} /></label><div className="row" style={{marginTop:10}}><button className="button primary" disabled={busy||service!=='ready'} onClick={()=>{setActive('cad');setMessage('Intent captured. Review the generated parameters before executing CAD.')}}>UNDERSTAND INTENT</button><button className="button" onClick={()=>{setIntent('');setMessage('Command cleared. Nothing executed.')}}>CLEAR</button></div></section>

    <nav className="panel" style={{marginTop:16}} aria-label="Engineering workflows"><div className="eyebrow">WORKFLOWS</div><div style={{display:'grid',gridTemplateColumns:'repeat(4,minmax(0,1fr))',gap:8,marginTop:10}}>{modules.map(([id,title,desc])=><button key={id} className={`button ${active===id?'primary':''}`} title={desc} onClick={()=>setActive(id)}>{title}</button>)}</div></nav>

    <section className="workspace-grid" style={{marginTop:16}}>
      <div className="panel">
        {active==='intent'&&<><h2>UNDERSTAND</h2><p className="muted">Natural language is the front door. The model may resolve intent and entities, but deterministic engineering remains authoritative for dimensions, tolerances and acceptance.</p><div className="result-row"><div><span className="muted">COMMAND</span><strong>{intent||'No command'}</strong></div></div></>}
        {active==='cad'&&<><h2>GENERATE CAD / STEP REQUIRED</h2><p className="muted">This action creates a real parametric solid, exports STEP, re-imports it through the CAD kernel and rejects the result if validation fails.</p><div className="formgrid"><label>Part name<input value={partName} onChange={e=>setPartName(e.target.value)}/></label><label>Revision<input value={revision} onChange={e=>setRevision(e.target.value)}/></label><label>Material<input value={material} onChange={e=>setMaterial(e.target.value)}/></label><label>Width mm<input type="number" value={width} onChange={e=>setWidth(Number(e.target.value))}/></label><label>Depth mm<input type="number" value={depth} onChange={e=>setDepth(Number(e.target.value))}/></label><label>Height mm<input type="number" value={height} onChange={e=>setHeight(Number(e.target.value))}/></label><label>Wall mm<input type="number" value={wall} step=".1" onChange={e=>setWall(Number(e.target.value))}/></label><label>Clearance mm<input type="number" value={clearance} step=".05" onChange={e=>setClearance(Number(e.target.value))}/></label></div><button className="button primary" disabled={busy||service!=='ready'} onClick={generateCad}>{busy?'Generating…':'GENERATE + VALIDATE STEP'}</button></>}
        {active==='analyze'&&<><h2>ANALYZE</h2><p className="muted">Run the deterministic engineering model. ML/uncertainty can inform the result; no model output bypasses the engineering gate.</p><button className="button primary" disabled={busy||service!=='ready'} onClick={runPrediction}>{busy?'Computing…':'RUN DETERMINISTIC CHECK'}</button></>}
        {['build','inspect','calibration','evidence','exports','projects','integrations','mcp','health'].includes(active)&&<><h2>{modules.find(m=>m[0]===active)?.[1].toUpperCase()}</h2><p className="muted">{modules.find(m=>m[0]===active)?.[2]}. This workflow now belongs to this authenticated workspace instead of a separate user-facing page.</p><div className="panel" style={{marginTop:12}}><strong>Project state is explicit.</strong><p className="muted">No fabricated output is shown. Execute the preceding required gate first when this workflow depends on it.</p></div></>}
      </div>
      <div className="panel"><h2>OUTPUT / EVIDENCE</h2>{!output?<div className="panel" style={{marginTop:12}}><strong>Nothing accepted yet.</strong><p className="muted">Choose an explicit action. Results appear here only after the service returns a valid response.</p></div>:<><div className="result-row"><div><span className="muted">TYPE</span><strong>{cad?'Validated STEP':'Engineering prediction'}</strong></div><div><span className="muted">STATUS</span><strong>{output.status||'returned'}</strong></div></div>{cad&&<View3D size={[width,depth,height]} deviation={0}/>}<details style={{marginTop:12}}><summary>Sanitized technical evidence</summary><pre className="provenance">{safeJson(output)}</pre></details></>}</div>
    </section>

    <section className="panel" style={{marginTop:16}}><div className="eyebrow">RECENT EXECUTION</div>{history.length?<ul>{history.slice(0,8).map((x,i)=><li key={i}>{x}</li>)}</ul>:<p className="muted">No execution has happened in this session.</p>}</section>

    <section className="panel" style={{marginTop:16}}><div className="eyebrow">RELEASE RULE</div><strong>Production manufacturing release requires validated STEP + evidence.</strong><p className="muted">The landing page never executes. This workspace is the execution surface after authentication.</p></section>
  </main>
}

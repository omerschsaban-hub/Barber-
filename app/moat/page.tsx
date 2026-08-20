import {createServerSupabase,hasSupabaseConfig} from '@/lib/supabase-server';

export const dynamic='force-dynamic';

const layers=[
  ['Physical-ground-truth','Physical outcomes, measurements, fit and assembly evidence',['print_outcomes','measured_dimensions','fit_tests','assembly_results']],
  ['Engineering decision','Requirements, decisions and design revisions',['user_requirements','design_revisions','engineering_decisions']],
  ['Failure library','Failures, false positives/negatives and edge cases',['failed_validations','false_positives','false_negatives','edge_case_discovery']],
  ['Calibration','Prediction-vs-reality, confidence and version drift',['prediction_reality','confidence_calibration','version_comparison']],
  ['Workflow','Common workflows, repeated actions and measured time savings',['common_workflows','repeated_actions','reported_time_savings']],
  ['MCP reliability','Tool success, failures, latency and retries',['mcp_success','mcp_failure','mcp_latency','mcp_retries']],
  ['Integration','Connected manufacturing, CAD, inspection and workflow events',['manufacturing_method','mcp_inputs','mcp_outputs','successful_geometry_patterns']],
  ['Verification / provenance','Evidence-backed validation and traceability',['validation_results','provenance','public_standards','manufacturer_datasheets']],
  ['Regression','Permanent tests generated from discovered failures',['regression_tests','edge_case_discovery']],
  ['Customer workflow','Corrections, complaints, retention and expansion signals',['customer_corrections','customer_complaints','retention','expansion']],
  ['Engineering speed','Prototype iterations and time-to-success',['prototype_iterations','time_to_success','reported_time_savings']],
  ['Trust / reliability','Validation quality and stable release evidence',['validation_results','prediction_reality','false_negatives']],
] as const;

export default async function Moat(){
  if(!hasSupabaseConfig()) return <main className="page"><div className="eyebrow">ENGINEERING INTELLIGENCE</div><h1 className="title">12 compounding moats</h1><div className="panel"><p className="muted">Supabase is not configured in this deployment.</p></div></main>;
  try{
    const s=await createServerSupabase();
    const {data:{user}}=await s.auth.getUser();
    if(!user) return <main className="page"><h1 className="title">Sign in required</h1></main>;
    const {data:rows,error}=await s.from('data_observations').select('source_key');
    if(error) throw error;
    const counts=new Map<string,number>();
    for(const r of rows||[]) counts.set(r.source_key,(counts.get(r.source_key)||0)+1);
    const scores=layers.map(([name,_desc,keys])=>({name,count:keys.reduce((n,k)=>n+(counts.get(k)||0),0)}));
    const total=scores.reduce((n,x)=>n+x.count,0);
    return <main className="page">
      <div className="row" style={{justifyContent:'space-between',alignItems:'end'}}><div><div className="eyebrow">FABRIENT / ENGINEERING INTELLIGENCE</div><h1 className="title">12 compounding moats</h1><p className="muted">Real engineering outcomes become evidence, calibration, regression coverage and faster workflows.</p></div><div className="panel" style={{minWidth:170}}><small>LINKED EVIDENCE</small><div style={{fontSize:28,fontWeight:700}}>{total}</div></div></div>
      <div className="grid grid2" style={{marginTop:24}}>{layers.map(([name,desc])=>{const item=scores.find(x=>x.name===name)!;return <section className="panel" key={name}><div className="row" style={{justifyContent:'space-between'}}><h2 style={{margin:0}}>{name}</h2><strong>{item.count}</strong></div><p className="muted">{desc}</p><div className="step"><div><b>{item.count>0?'ACTIVE EVIDENCE':'AWAITING EVIDENCE'}</b><br/><small>{item.count>0?'This moat is connected to stored engineering observations.':'The product is ready to collect this evidence.'}</small></div></div></section>})}</div>
      <section className="panel" style={{marginTop:24}}><div className="eyebrow">COMPOUNDING LOOP</div><h2>Requirement → design → prediction → validation → manufacturing → physical result → correction → regression → calibration → better workflow</h2><p className="muted">No automatic engineering-rule change is promoted from telemetry alone. Verified changes remain behind the existing validation and release gates.</p></section>
    </main>;
  }catch{return <main className="page"><h1 className="title">Engineering intelligence unavailable</h1><div className="panel"><p className="muted">The moat dashboard could not read the current evidence store.</p></div></main>}
}

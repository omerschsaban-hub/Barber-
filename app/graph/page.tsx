import {createServerSupabase,hasSupabaseConfig} from '@/lib/supabase-server';

const agents=['Context / evidence retrieval','Physics / deterministic baseline','Measurement / CV extraction','Calibration / system identification','Residual ML / validation','Uncertainty / risk gate','Experiment / next selection','Critic / engineering honesty'];
const technicalSteps=['Engineering input','Structured problem','Physics simulation','Deterministic checks','Uncertainty/domain randomization','Real inspection measurement','System identification','Residual ML','Validated uncertainty','Next experiment'];

export default async function Graph(){
  if(!hasSupabaseConfig())return <main className="page"><h1 className="title">Sign in required</h1></main>;
  try{
    const s=await createServerSupabase();
    const {data:{user}}=await s.auth.getUser();
    if(!user)return <main className="page"><h1 className="title">Sign in required</h1></main>;
    return <main className="page">
      <div className="eyebrow">FABRIENT / ENGINEERING WORKSPACE</div>
      <h1 className="title">Give Fabrient the job. It handles the engineering.</h1>
      <p className="lede" style={{maxWidth:720}}>You do not need to manage an agent graph or choose individual tools. Describe the outcome, provide the design and measurements when needed, and Fabrient keeps the work moving while showing you exactly what needs your attention.</p>
      <div className="grid grid2" style={{marginTop:24}}>
        <div className="panel"><h2>YOU</h2>{[['01','Describe the outcome','Tell Fabrient what you need built or verified.'],['02','Provide what you have','Upload the design, machine details, or physical measurements.'],['03','Review only important decisions','Fabrient explains blockers and asks before consequential changes.'],['04','Release when ready','You stay in control of the final consequential release.']].map(([n,title,copy])=><div className="step" key={n}><div><b>{n} / {title}</b><br/><small>{copy}</small></div></div>)}</div>
        <div className="panel"><h2>FABRIENT</h2>{[['01','Understands the job','Turns the request into a structured, resumable engineering job.'],['02','Checks the design','Runs deterministic engineering checks instead of guessing.'],['03','Acts within boundaries','Chooses the next bounded action and records what happened.'],['04','Proves the result','Carries evidence, provenance, uncertainty and release gates through the job.']].map(([n,title,copy])=><div className="step" key={n}><div><b>{n} / {title}</b><br/><small>{copy}</small></div></div>)}</div>
      </div>
      <div className="grid grid2" style={{marginTop:24}}>
        <div className="panel"><h2>EXECUTION DETAILS</h2>{technicalSteps.map((x,i)=><div className="step" key={x}><div><b>{String(i+1).padStart(2,'0')} / {x}</b><br/><small>{i<4?'deterministic':'requires real evidence'}</small></div></div>)}</div>
        <div className="panel"><h2>ENGINEERING AGENTS</h2>{agents.map(x=><div className="step" key={x}><div><b>{x}</b><br/><small>bounded role · structured evidence · no unchecked engineering truth</small></div></div>)}</div>
      </div>
    </main>
  }catch{return <main className="page"><h1 className="title">Sign in required</h1></main>}
}

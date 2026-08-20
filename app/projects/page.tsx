import Link from 'next/link';
import {createServerSupabase, hasSupabaseConfig} from '@/lib/supabase-server';

export const dynamic = 'force-dynamic';

export default async function Projects(){
  if(!hasSupabaseConfig()) return <main className="page"><div className="eyebrow">WORKSPACE</div><h1 className="title">Projects</h1><div className="panel"><p className="muted">Project storage is not configured in this deployment. Geometry, risk-map, CV and engineering workflows remain available without project persistence.</p></div></main>;
  const s=await createServerSupabase();
  const {data:{user}}=await s.auth.getUser();
  if(!user)return <main className="page"><h1 className="title">Sign in required</h1><Link className="button" href="/login">Continue with Google</Link></main>;
  const {data:projects}=await s.from('projects').select('*').order('created_at',{ascending:false});
  return <main className="page"><div className="row" style={{justifyContent:'space-between'}}><div><div className="eyebrow">WORKSPACE</div><h1 className="title">Projects</h1></div><Link className="button" href="/projects/new">New project</Link></div><div className="grid" style={{marginTop:24}}>{(projects||[]).map(p=><Link className="panel" href={`/projects/${p.id}`} key={p.id}><h2>{p.name}</h2><p className="muted">{p.description||'No description'}</p></Link>)}{!(projects||[]).length&&<div className="panel"><p className="muted">No projects yet. Start with a machine and a real inspection dataset.</p></div>}</div></main>;
}

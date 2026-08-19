import './globals.css';
import Link from 'next/link';
import { createServerSupabase } from '@/lib/supabase-server';
export const metadata={title:'Fabrient — Engineering Release System',description:'From part definition to verified manufacturing release.'};
export default async function RootLayout({children}:{children:React.ReactNode}){
  let user:null|{email?:string}=null;
  if(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY){
    try { const supabase=await createServerSupabase(); const {data}=await supabase.auth.getUser(); user=data.user; } catch { user=null; }
  }
  return <html lang="en"><body><header className="topbar"><Link href="/" className="brand">FABRIENT</Link><nav><Link href="/workspace">Workspace</Link><Link href="/projects">Projects</Link><Link href="/manufacturing">Build</Link><Link href="/import">Inspect</Link></nav><div className="nav-secondary"><Link href="/geometry">Geometry</Link><Link href="/calibration">Calibration</Link><Link href="/graph">Evidence</Link><Link href="/records">Exports</Link></div><div>{user?<span className="user">{user.email}</span>:<Link href="/login" className="button">Sign in</Link>}</div></header>{children}</body></html>}

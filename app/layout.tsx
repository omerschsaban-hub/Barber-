import './globals.css';
import { createServerSupabase } from '@/lib/supabase-server';
import Link from 'next/link';

export const metadata = { title: 'Fabrient', description: 'Engineering-grade dimensional drift intelligence' };

export default async function RootLayout({children}:{children:React.ReactNode}) {
  const supabase = await createServerSupabase();
  const { data:{user} } = await supabase.auth.getUser();
  return <html lang="en"><body><header className="topbar"><Link href="/" className="brand">FABRIENT</Link><nav><Link href="/projects">Projects</Link><Link href="/import">Import</Link><Link href="/calibration">Calibration</Link><Link href="/experiments">Experiments</Link></nav><div>{user ? <span className="user">{user.email}</span> : <Link href="/login" className="button">Sign in</Link>}</div></header>{children}</body></html>;
}
'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { createBrowserSupabase } from '@/lib/supabase-browser';

export default function AppHeader() {
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    let subscription: { unsubscribe: () => void } | null = null;

    // Auth must never be on the critical rendering path. A malformed client
    // configuration, auth callback, or SDK failure must leave the shell usable.
    try {
      const supabase = createBrowserSupabase();
      if (!supabase) return () => { mounted = false; };

      void Promise.race([
        supabase.auth.getSession(),
        new Promise<never>((_, reject) => setTimeout(() => reject(new Error('auth-timeout')), 2500)),
      ])
        .then(({ data }: any) => {
          if (mounted) setEmail(data?.session?.user?.email ?? null);
        })
        .catch(() => {
          // Auth is optional for the public shell.
        });

      try {
        const result = supabase.auth.onAuthStateChange((_event: any, session: any) => {
          if (mounted) setEmail(session?.user?.email ?? null);
        });
        subscription = result?.data?.subscription ?? null;
      } catch {
        subscription = null;
      }
    } catch {
      // Never allow auth initialization to blank the application.
    }

    return () => {
      mounted = false;
      try { subscription?.unsubscribe(); } catch {}
    };
  }, []);

  return <header className="topbar">
    <Link href="/" className="brand">FABRIENT</Link>
    <nav>
      <Link href="/workspace">Workspace</Link><Link href="/projects">Projects</Link><Link href="/manufacturing">Build</Link><Link href="/import">Inspect</Link>
    </nav>
    <div className="nav-secondary">
      <Link href="/geometry">Geometry</Link><Link href="/calibration">Calibration</Link><Link href="/graph">Evidence</Link><Link href="/records">Exports</Link><Link href="/integrations">Integrations</Link>
    </div>
    <div>{email ? <span className="user">{email}</span> : <Link href="/login" className="button">Sign in</Link>}</div>
  </header>;
}

'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { createBrowserSupabase } from '@/lib/supabase-browser';

export default function AppHeader() {
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const supabase = createBrowserSupabase();
    if (!supabase) return;

    let mounted = true;
    supabase.auth.getSession().then(({ data }) => {
      if (mounted) setEmail(data.session?.user?.email ?? null);
    }).catch(() => {});

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, session) => {
      if (mounted) setEmail(session?.user?.email ?? null);
    });

    return () => {
      mounted = false;
      subscription.subscription.unsubscribe();
    };
  }, []);

  return (
    <header className="topbar">
      <Link href="/" className="brand">FABRIENT</Link>
      <nav>
        <Link href="/workspace">Workspace</Link>
        <Link href="/projects">Projects</Link>
        <Link href="/manufacturing">Build</Link>
        <Link href="/import">Inspect</Link>
      </nav>
      <div className="nav-secondary">
        <Link href="/geometry">Geometry</Link>
        <Link href="/calibration">Calibration</Link>
        <Link href="/graph">Evidence</Link>
        <Link href="/records">Exports</Link>
      </div>
      <div>{email ? <span className="user">{email}</span> : <Link href="/login" className="button">Sign in</Link>}</div>
    </header>
  );
}

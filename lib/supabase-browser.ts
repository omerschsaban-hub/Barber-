import { createBrowserClient } from '@supabase/ssr';

export function createBrowserSupabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null;

  // Auth is optional for the public app shell. A bad/missing deployment
  // variable must never crash the client after first paint.
  try {
    return createBrowserClient(url, key);
  } catch {
    return null;
  }
}

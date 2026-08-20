'use client';

import { useEffect } from 'react';

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // Keep the production app recoverable if a client-side route crashes.
    // The error itself is intentionally not rendered to avoid exposing internals.
  }, []);

  return (
    <main className="page" role="alert">
      <section className="panel" style={{ maxWidth: 720, margin: '80px auto' }}>
        <div className="section-kicker">APPLICATION RECOVERY</div>
        <h1 style={{ marginTop: 0 }}>The app hit a temporary client error.</h1>
        <p className="muted">The engineering workspace is still available. Reload the interface and try again.</p>
        <button className="button primary" onClick={() => reset()}>Reload workspace</button>
      </section>
    </main>
  );
}

'use client';

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: '#0a0b09', color: '#f0f1eb', fontFamily: 'system-ui, sans-serif' }}>
        <main style={{ maxWidth: 720, margin: '0 auto', padding: '96px 24px' }}>
          <div style={{ border: '1px solid #2a3029', borderRadius: 8, background: '#10130f', padding: 28 }}>
            <div style={{ color: '#8fe36a', fontSize: 11, fontWeight: 800, letterSpacing: '.12em' }}>FABRIENT / RECOVERY</div>
            <h1 style={{ margin: '12px 0', fontSize: 32 }}>The workspace hit a temporary error.</h1>
            <p style={{ color: '#a2a89f', lineHeight: 1.6 }}>The application shell is still available. Reload to recover the workspace.</p>
            <button onClick={() => reset()} style={{ marginTop: 12, border: '1px solid #8fe36a', borderRadius: 6, padding: '10px 14px', background: '#8fe36a', color: '#10140f', fontWeight: 800, cursor: 'pointer' }}>Reload workspace</button>
          </div>
        </main>
      </body>
    </html>
  );
}

'use client';

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: '#eff7c8', color: '#173b27', fontFamily: 'system-ui, sans-serif' }}>
        <main style={{ maxWidth: 720, margin: '0 auto', padding: '96px 24px' }}>
          <div style={{ border: '2px solid #31a852', borderRadius: 20, background: '#f8f3a6', padding: 28, boxShadow: '7px 7px 0 #8bbf4a' }}>
            <div style={{ color: '#176b3a', fontSize: 11, fontWeight: 800, letterSpacing: '.12em' }}>FABRIENT / RECOVERY</div>
            <h1 style={{ margin: '12px 0', fontSize: 32 }}>The application hit a temporary error.</h1>
            <p style={{ color: '#4f713d', lineHeight: 1.6 }}>The production shell crashed before it could render normally. Reload to retry.</p>
            <button onClick={() => reset()} style={{ marginTop: 12, border: '2px solid #176b3a', borderRadius: 14, padding: '11px 16px', background: '#31a852', color: '#f8f3a6', fontWeight: 800, cursor: 'pointer' }}>Reload workspace</button>
          </div>
        </main>
      </body>
    </html>
  );
}

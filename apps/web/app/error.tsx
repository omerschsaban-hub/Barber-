'use client'

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="error-screen">
      <section className="error-card">
        <div className="eyebrow">FABRIENT / RECOVERY</div>
        <h1>The workspace hit a runtime error.</h1>
        <p className="lede">
          The application is still alive. This recovery screen replaces the blank page and lets you retry safely.
        </p>
        {process.env.NODE_ENV !== 'production' && error?.message ? <pre>{error.message}</pre> : null}
        <button onClick={() => reset()}>Retry workspace</button>
      </section>
    </main>
  )
}

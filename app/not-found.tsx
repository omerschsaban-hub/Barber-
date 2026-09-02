import Link from 'next/link'

export default function NotFound() {
  return (
    <main className="page-shell" style={{ minHeight: '70vh', display: 'grid', placeItems: 'center', padding: '64px 24px' }}>
      <section className="card" style={{ maxWidth: 720, width: '100%' }}>
        <p style={{ letterSpacing: '.12em', fontSize: 12, fontWeight: 700 }}>FABRIENT / 404</p>
        <h1>That page does not exist.</h1>
        <p>The address may be wrong, or the resource may have been removed. Nothing was silently redirected.</p>
        <Link className="cad-button cad-button-main" href="/">Back to Fabrient</Link>
      </section>
    </main>
  )
}

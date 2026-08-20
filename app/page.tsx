import Link from 'next/link'

const loop = [
  ['Define', 'Requirements, dimensions and evidence boundary.'],
  ['Validate', 'Deterministic DFM and geometry checks expose concrete failures.'],
  ['Verify', 'Real measurements and simulation evidence are kept separate.'],
  ['Release', 'A manufacturing package is produced only when its gates are satisfied.'],
]

export default function Home() {
  return (
    <main className="page">
      <section className="hero-grid">
        <div className="hero-copy">
          <div className="eyebrow">FABRIENT / ENGINEERING RELEASE</div>
          <h1 className="title">A traceable path from part requirements to a build you can inspect.</h1>
          <p className="hero-sub">
            Fabrient keeps geometry, deterministic checks, physical observations, uncertainty and release decisions in one engineering record. Claims stay tied to evidence instead of presentation effects.
          </p>
          <div className="hero-actions">
            <Link className="button primary" href="/manufacturing">Start a build</Link>
            <Link className="button" href="/workspace">Open workspace</Link>
          </div>
        </div>
        <aside className="release-summary" aria-label="Release workflow">
          <div className="summary-heading">RELEASE RECORD</div>
          <dl>
            <div><dt>Geometry</dt><dd>Required</dd></div>
            <div><dt>DFM checks</dt><dd>Deterministic</dd></div>
            <div><dt>Physical evidence</dt><dd>Ground truth</dd></div>
            <div><dt>Uncertainty</dt><dd>Explicit</dd></div>
            <div><dt>Final acceptance</dt><dd>Human gate</dd></div>
          </dl>
        </aside>
      </section>

      <section className="workflow-section">
        <div className="section-kicker">THE ENGINEERING RECORD</div>
        <div className="workflow-list">
          {loop.map(([name, description], index) => (
            <article className="workflow-row" key={name}>
              <div className="workflow-index">0{index + 1}</div>
              <h2>{name}</h2>
              <p className="muted">{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel release-note">
        <div>
          <div className="section-kicker">DESIGN RULE</div>
          <h2>Evidence before polish.</h2>
          <p className="muted">The interface intentionally avoids decorative status claims, invented customer proof, unnecessary motion and generic AI-product patterns. Engineering state should be understandable from the record itself.</p>
        </div>
        <Link className="button" href="/records">View records</Link>
      </section>
    </main>
  )
}

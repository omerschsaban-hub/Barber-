import Link from 'next/link'

const loop = [
  ['01', 'Define', 'Requirements, dimensions and evidence boundary.'],
  ['02', 'Validate', 'Deterministic DFM and geometry checks expose concrete failures.'],
  ['03', 'Verify', 'Real measurements and simulation evidence stay separate.'],
  ['04', 'Release', 'A manufacturing package is produced only when its gates are satisfied.'],
]

export default function Home() {
  return (
    <main className="page home-page">
      <section className="hero-grid hero-scene">
        <div className="hero-copy">
          <div className="eyebrow">FABRIENT / PHYSICAL ENGINEERING</div>
          <h1 className="title">Turn an idea into a part that is ready to build.</h1>
          <p className="hero-sub">A visual engineering workspace for geometry, deterministic checks, physical evidence and manufacturing release — without fake AI theatre.</p>
          <div className="hero-actions">
            <Link className="button primary" href="/manufacturing">Start a build <span>↗</span></Link>
            <Link className="button" href="/workspace">Open workspace</Link>
            <Link className="button" href="/engineering">Engineering Center</Link>
          </div>
          <div className="hero-proof"><span className="signal-dot" /> Evidence-first. Deterministic. Buildable.</div>
        </div>

        <aside className="hero-object" aria-label="Fabrient 3D engineering object">
          <div className="object-label label-a">GEOMETRY / LOCKED</div>
          <div className="object-label label-b">DFM / PASS</div>
          <div className="object-label label-c">EVIDENCE / LIVE</div>
          <div className="cube-stage">
            <div className="cube">
              <span className="cube-face front" /><span className="cube-face back" /><span className="cube-face right" />
              <span className="cube-face left" /><span className="cube-face top" /><span className="cube-face bottom" />
            </div>
          </div>
          <div className="orbit orbit-one" /><div className="orbit orbit-two" />
          <div className="object-caption"><b>FABRIENT CORE</b><span>traceable physical release</span></div>
        </aside>
      </section>

      <section className="signal-strip" aria-label="Engineering signals">
        <div><span>01</span><b>Geometry</b><small>Measured inputs</small></div>
        <div><span>02</span><b>DFM</b><small>Deterministic gates</small></div>
        <div><span>03</span><b>Evidence</b><small>Physical ground truth</small></div>
        <div><span>04</span><b>Release</b><small>Manufacturing-ready</small></div>
      </section>

      <section className="workflow-section">
        <div className="section-heading"><div><div className="section-kicker">THE ENGINEERING LOOP</div><h2>From geometry to release.</h2></div><span className="section-count">4 gates / 0 guesswork</span></div>
        <div className="workflow-list">
          {loop.map(([index, name, description]) => (
            <article className="workflow-row" key={name}>
              <div className="workflow-index">{index}</div><div className="workflow-name"><span className="workflow-marker" />{name}</div>
              <p className="muted">{description}</p><span className="workflow-arrow">→</span>
            </article>
          ))}
        </div>
      </section>

      <section className="panel release-note">
        <div><div className="section-kicker">DESIGN PRINCIPLE</div><h2>Technical, playful, and honest.</h2><p className="muted">3D depth comes from lightweight CSS perspective and transforms, not a heavy WebGL scene. The UI stays fast, responsive and readable while the engineering record remains the source of truth.</p></div>
        <div className="row"><Link className="button" href="/records">View records</Link><Link className="button primary" href="/engineering">Run advanced engineering</Link></div>
      </section>
    </main>
  )
}

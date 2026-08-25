import Link from 'next/link'

const REAL_PHOTO = 'https://images.pexels.com/photos/22491107/pexels-photo-22491107.jpeg?auto=compress&cs=tinysrgb&w=1600'

export default function Home() {
  return (
    <main className="cad-home">
      <section className="cad-hero friendly-hero">
        <div className="cad-intro">
          <div className="cad-kicker"><span className="live-dot" /> FABRIENT</div>
          <h1>Engineer physical products<br /><em>from intent to evidence.</em></h1>
          <p>Describe what you want. After you sign in, Fabrient gives you one workspace for CAD, deterministic engineering, ML, inspection, evidence and manufacturing release.</p>
          <div className="cad-actions">
            <Link href="/login?redirect=/workspace" className="cad-button cad-button-main">GET STARTED <span>→</span></Link>
            <Link href="/login?redirect=/workspace" className="cad-button">LOG IN</Link>
          </div>
          <div className="friendly-note"><span className="live-dot" /> Informational entry point only. Nothing is analyzed, generated, changed or submitted here.</div>
        </div>
        <div className="cad-stage friendly-stage" aria-label="Real electronics manufacturing photograph">
          <img src={REAL_PHOTO} alt="Real 3D printer mechanism used for precision manufacturing" loading="eager" referrerPolicy="no-referrer" />
          <div className="photo-credit">Real manufacturing photo · Pexels</div>
          <div className="cad-tag tag-pass">REAL HARDWARE</div>
          <div className="cad-tag tag-rev">ENGINE → EVIDENCE</div>
        </div>
      </section>
      <section className="cad-work">
        <div className="cad-section-head"><div><span>ONE WORKSPACE</span><h2>Everything important stays together.</h2></div></div>
        <div className="cad-grid">
          <article className="cad-card large"><header><span>01 / UNDERSTAND</span><b>INTENT</b></header><div className="card-value">Use normal language.</div><p>Fabrient resolves products, constraints and engineering intent before an execution begins.</p></article>
          <article className="cad-card"><header><span>02 / GENERATE</span><b>CAD</b></header><div className="card-value">Validated STEP.</div><p>Manufacturing release is gated on real CAD validation.</p></article>
          <article className="cad-card"><header><span>03 / VERIFY</span><b>EVIDENCE</b></header><div className="card-value">No fabricated answers.</div><p>Deterministic checks, ML outputs and provenance stay attached to the revision.</p></article>
          <article className="cad-card wide-card"><header><span>04 / RELEASE</span><b className="yellow-state">PHYSICAL LOOP</b></header><div className="release-line"><strong>Build → inspect → learn → re-verify</strong><span>one project history</span></div><p>After login, these workflows are presented as one continuous engineering workspace rather than a collection of disconnected pages.</p></article>
        </div>
      </section>
      <section className="friendly-bottom"><strong>Clear on the outside. Serious underneath.</strong><span>Sign in to enter the execution workspace.</span></section>
    </main>
  )
}

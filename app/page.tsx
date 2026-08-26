import Link from 'next/link'

const REAL_PHOTO = 'https://images.pexels.com/photos/22491107/pexels-photo-22491107.jpeg?auto=compress&cs=tinysrgb&w=1600'

export default function Home() {
  return (
    <main className="cad-home">
      <section className="cad-hero friendly-hero">
        <div className="cad-intro">
          <div className="cad-kicker"><span className="live-dot" /> FABRIENT / ENGINEERING SYSTEM</div>
          <h1>From intent<br /><em>to physical evidence.</em></h1>
          <p>Fabrient is an engineering system for turning bounded physical-product jobs into verified outcomes. Natural language coordinates the work; deterministic computation, real measurements, machine/process models and explicit release gates decide what can actually be trusted.</p>
          <div className="cad-actions">
            <Link href="/login?redirect=/workspace" className="cad-button cad-button-main">ENTER WORKSPACE <span>→</span></Link>
            <Link href="/login?redirect=/workspace" className="cad-button">VIEW THE SYSTEM</Link>
          </div>
          <div className="friendly-note"><span className="live-dot" /> AI proposes and coordinates. Engineering authorities calculate, measure, validate and refuse unsupported conclusions.</div>
        </div>
        <div className="cad-stage friendly-stage" aria-label="Real electronics manufacturing photograph">
          <img src={REAL_PHOTO} alt="Real 3D printer mechanism used for precision manufacturing" loading="eager" referrerPolicy="no-referrer" />
          <div className="photo-credit">Real manufacturing photo · Pexels</div>
          <div className="cad-tag tag-pass">PHYSICAL SYSTEM</div>
          <div className="cad-tag tag-rev">SIM → REAL → RELEASE</div>
        </div>
      </section>

      <section className="cad-pipeline technical-pipeline" aria-label="Fabrient engineering pipeline">
        {[
          ['01', 'DEFINE', 'Intent, assets, constraints, evidence'],
          ['02', 'ANALYZE', 'Physics, geometry, DFM, measurements'],
          ['03', 'LEARN', 'System ID, residual ML, uncertainty'],
          ['04', 'VERIFY', 'Held-out validation, gates, provenance'],
          ['05', 'BUILD', 'Physical experiment + inspection'],
          ['06', 'RELEASE', 'Manufacturing package + audit trail'],
        ].map(([n, title, text]) => (
          <div className="cad-stage-row" key={n}><span className="stage-num">{n}</span><strong>{title}</strong><small>{text}</small><i className="stage-line" /></div>
        ))}
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>THE SYSTEM</span><h2>One engineering loop, with different authorities.</h2></div></div>
        <div className="system-map">
          <div className="system-column system-ai"><span>LANGUAGE / ORCHESTRATION</span><strong>LLM intent + bounded agents</strong><p>Normalizes the request, gathers relevant context, explains decisions and selects bounded next actions. It does not invent engineering numbers or evidence.</p><div className="system-code">context → plan → act → observe → explain</div></div>
          <div className="system-connector">→</div>
          <div className="system-column"><span>ENGINEERING AUTHORITIES</span><strong>Deterministic computation</strong><p>Physics baselines, dimensional checks, geometry validation, DFM gates and release rules produce reproducible outputs from explicit inputs.</p><div className="system-code">units · ranges · tolerances · geometry · topology</div></div>
          <div className="system-connector">→</div>
          <div className="system-column system-evidence"><span>REALITY</span><strong>Measurement + feedback</strong><p>STEP/CAD evidence, inspection records, physical measurements and build outcomes feed the next bounded engineering decision.</p><div className="system-code">observe → measure → compare → update</div></div>
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>MODELS / ALGORITHMS</span><h2>ML sits behind the physics, not above it.</h2></div></div>
        <div className="model-grid">
          <article className="model-card"><span>01 / SYSTEM IDENTIFICATION</span><h3>Ridge regression</h3><p>Machine/process effects are fitted from real observations using layer height, print speed, nozzle temperature, ambient temperature, humidity and axis. Leave-one-out validation reports held-out MAE and residual spread.</p><div className="model-spec">Ridge α = 1.0 · real observations only · LOO validation</div></article>
          <article className="model-card"><span>02 / RESIDUAL ML</span><h3>Interpretable correction layer</h3><p>ML models the remaining error after a deterministic baseline rather than replacing the baseline. Residuals stay visible so a recommendation can be traced back to physics, measurement and learned error.</p><div className="model-spec">physics baseline + residual model + held-out evidence</div></article>
          <article className="model-card"><span>03 / UNCERTAINTY</span><h3>Combined error budget</h3><p>Physics uncertainty, measurement uncertainty, model uncertainty and empirical residual spread are combined to produce a bounded 95% interval. Insufficient real observations produce a refusal instead of fake confidence.</p><div className="model-spec">σ = √(σphysics² + σmeasurement² + σmodel² + σresidual²)</div></article>
          <article className="model-card"><span>04 / COMPUTER VISION</span><h3>Scale-gated measurement</h3><p>OpenCV primitives can detect line candidates and measure an explicitly referenced feature in pixels. Image size, contrast and sharpness are checked first; a physical reference establishes scale.</p><div className="model-spec">Canny + HoughLinesP · explicit mm/px scale · quality gates</div></article>
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>GEOMETRY → MANUFACTURING</span><h2>CAD is an engineering artifact, not an AI picture.</h2></div></div>
        <div className="cad-grid technical-cards">
          <article className="cad-card"><header><span>CAD KERNEL</span><b>CadQuery / OCCT</b></header><div className="card-value">Deterministic geometry.</div><p>Parametric geometry is generated through a CAD kernel. STEP exchange format is checked, then topology/round-trip validation gates further engineering work.</p></article>
          <article className="cad-card"><header><span>DFM</span><b>RULES + MEASUREMENTS</b></header><div className="card-value">Find → fix → verify.</div><p>Manufacturing limits are evaluated against the actual part context. Deterministic self-fixes can be applied; consequential geometry/topology changes remain human-gated.</p></article>
          <article className="cad-card"><header><span>PHYSICAL LOOP</span><b>SIM → REAL</b></header><div className="card-value">Evidence compounds.</div><p>Inspection records, fit tests, measured dimensions, print outcomes and prediction-versus-reality deltas become provenance-bearing observations for later decisions.</p></article>
          <article className="cad-card wide-card"><header><span>RELEASE</span><b className="yellow-state">AUDITABLE OUTPUT</b></header><div className="release-line"><strong>STEP + DFM report + build guide + inspection plan</strong><span>release only after gates pass</span></div><div className="release-bar"><i /></div><p>A release is a usable manufacturing package, not a green UI badge. The package carries revision, provenance, validation state and the remaining blockers.</p></article>
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>DATA FLYWHEEL</span><h2>The product gets better from reality.</h2></div></div>
        <div className="flywheel-row">
          <div><b>DESIGN</b><span>requirements · CAD · revisions</span></div><i>→</i><div><b>PREDICT</b><span>physics · system ID · residuals</span></div><i>→</i><div><b>BUILD</b><span>machine · material · process</span></div><i>→</i><div><b>MEASURE</b><span>inspection · fit · outcomes</span></div><i>→</i><div><b>LEARN</b><span>prediction/reality · failures · corrections</span></div>
        </div>
        <p className="section-note">The flywheel is provenance-first: observations are normalized, consent-gated, hashed for deduplication and stored with their source context. Synthetic data is not presented as calibration evidence.</p>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>AGENT NATIVE</span><h2>Humans and agents operate the same engineering system.</h2></div></div>
        <div className="agent-story"><div className="agent-node"><span>INPUT</span><strong>“Make this enclosure fit the board and be manufacturable.”</strong></div><div className="agent-arrow">↓</div><div className="agent-node"><span>BOUNDED GRAPH</span><strong>Context → Physics → Validation → Measurement → System ID → Residual ML → Risk gate → Experiment</strong></div><div className="agent-arrow">↓</div><div className="agent-node"><span>OUTPUT</span><strong>Verified artifact, evidence, blocker or explicit request for human approval.</strong></div></div>
        <div className="prohibition-strip"><span>NO FABRICATED MEASUREMENTS</span><span>NO FABRICATED CONFIDENCE</span><span>NO AUTOMATIC TOLERANCE OVERRIDES</span><span>NO UNBOUNDED EXECUTION</span></div>
      </section>

      <section className="friendly-bottom technical-bottom"><strong>Serious engineering underneath.</strong><span>Define the job. Bring evidence. Let the system prove what it can.</span><Link href="/login?redirect=/workspace" className="cad-button cad-button-main">ENTER FABRIENT →</Link></section>
    </main>
  )
}

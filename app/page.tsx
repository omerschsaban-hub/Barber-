import Image from 'next/image'
import Link from 'next/link'
import { ENTERPRISE_CONTACT, FABRINAT_PLANS, planUsageLabel } from '@/lib/fabrinat-plans'

const PLAN_ORDER = ['free', 'hobbyist', 'startup', 'enterprise'] as const
const CONTACT_EMAIL = ENTERPRISE_CONTACT.email
const CONTACT_PHONE = ENTERPRISE_CONTACT.phone
const REAL_PHOTO = 'https://images.pexels.com/photos/22491107/pexels-photo-22491107.jpeg?auto=compress&cs=tinysrgb&w=1600'

export default function Home() {
  return (
    <main className="cad-home presale-home">
      <header className="presale-nav">
        <Link href="/" className="brand">FABRIENT</Link>
        <nav aria-label="Main navigation">
          <a href="#problem">Problem</a>
          <a href="#solution">Solution</a>
          <a href="#mcp">MCP</a>
          <a href="#pricing">Pricing</a>
          <a href={`mailto:${CONTACT_EMAIL}`}>Contact</a>
        </nav>
      </header>

      <section className="cad-hero presale-hero">
        <div className="cad-intro">
          <div className="cad-kicker"><span className="live-dot" /> FABRIENT / SIM → REAL</div>
          <h1>Build physical products with an engineering loop that follows the part into the real world.</h1>
          <p>Fabrient connects engineering intent, deterministic computation, AI agents, manufacturing data and physical measurements in one workflow. Teams can inspect what was designed, what was built and what changed between the two.</p>
          <div className="cad-actions">
            <a href={`mailto:${CONTACT_EMAIL}?subject=Fabrient%20presale`} className="cad-button cad-button-main">TALK TO US <span>→</span></a>
            <a href={`tel:${CONTACT_PHONE}`} className="cad-button">CALL US <span>→</span></a>
            <a href="#solution" className="cad-button">SEE HOW IT WORKS</a>
          </div>
        </div>
        <div className="cad-stage friendly-stage" aria-label="Real manufacturing photograph">
          <Image src={REAL_PHOTO} alt="A real machine used for precision manufacturing" width={1600} height={1067} priority sizes="(max-width: 900px) 100vw, 50vw" />
          <div className="photo-credit">Engineering decisions meet physical production.</div>
          <div className="cad-tag tag-pass">REAL-WORLD ENGINEERING</div>
          <div className="cad-tag tag-rev">DESIGN → BUILD → MEASURE</div>
        </div>
      </section>

      <section className="cad-work launch-demo-section" aria-labelledby="launch-demo-title">
        <div className="cad-section-head">
          <div><span>FABRIENT IN ACTION</span><h2 id="launch-demo-title">See the engineering loop before you use it.</h2></div>
          <p>A short walkthrough of how Fabrient connects engineering intent, computation and physical evidence into one traceable workflow.</p>
        </div>
        <div className="launch-demo-frame">
          <video controls preload="metadata" playsInline aria-label="Fabrient launch demo">
            <source src="https://files.manuscdn.com/user_upload_by_module/session_file/310519663321590917/uilhFdzHJgyMSihq.mp4" type="video/mp4" />
            Your browser does not support the video element. <a href="https://files.manuscdn.com/user_upload_by_module/session_file/310519663321590917/uilhFdzHJgyMSihq.mp4">Watch the Fabrient launch demo</a>.
          </video>
        </div>
      </section>

      <section id="problem" className="cad-work technical-section">
        <div className="cad-section-head">
          <div><span>THE PROBLEM</span><h2>Every physical build adds information to the engineering process.</h2></div>
          <p>CAD, simulation and specifications describe the intended product. Manufacturing introduces tolerances, material behavior, assembly conditions, process variation and measurement results. Those observations need to stay connected to the engineering decisions that created the part.</p>
        </div>
        <div className="reality-flow">
          <div><small>01</small><strong>Design</strong><p>Capture geometry, dimensions, constraints and engineering intent.</p></div>
          <i>→</i>
          <div><small>02</small><strong>Build</strong><p>Manufacture the physical product under real process conditions.</p></div>
          <i>→</i>
          <div><small>03</small><strong>Measure</strong><p>Collect inspection results, images, tests and physical observations.</p></div>
          <i>→</i>
          <div><small>04</small><strong>Improve</strong><p>Use the measured result to guide the next engineering decision.</p></div>
        </div>
      </section>

      <section id="solution" className="cad-work technical-section">
        <div className="cad-section-head">
          <div><span>THE SOLUTION</span><h2>A connected engineering workflow from design to physical evidence.</h2></div>
          <p>Fabrient organizes the work around the engineering state of the product. Computation, agent actions and physical observations remain traceable to the revision and decision they belong to.</p>
        </div>
        <div className="capability-grid presale-grid">
          <article><span>ENGINEERING BASELINE</span><h3>Define what the design should do.</h3><p>Run deterministic geometry, dimensions, constraints and manufacturing checks against a known engineering baseline.</p></article>
          <article><span>PHYSICAL DATA</span><h3>Bring production results into the workflow.</h3><p>Store measurements, inspection records and observations with the product revision and the source of the data.</p></article>
          <article><span>REVISION ANALYSIS</span><h3>Understand the difference between design and build.</h3><p>Compare expected and measured results across revisions so engineers can identify recurring issues and make informed changes.</p></article>
        </div>
      </section>

      <section id="mcp" className="cad-work technical-section mcp-section">
        <div className="cad-section-head">
          <div><span>FOR AI AGENTS</span><h2>Give engineering agents structured tools and reliable results.</h2></div>
          <p>Fabrient MCP connects agents to authenticated engineering operations. Agents can request calculations, inspect project state, run supported checks and receive structured results with units, validation state and engineering context.</p>
        </div>
        <div className="agent-story">
          <div className="agent-node"><span>AGENT</span><strong>Reads the engineering task and selects the required operation.</strong></div>
          <div className="agent-arrow">↓</div>
          <div className="agent-node"><span>FABRIENT MCP</span><strong>Executes authenticated tools and returns structured engineering results.</strong></div>
          <div className="agent-arrow">↓</div>
          <div className="agent-node"><span>ENGINEERING STATE</span><strong>Stores computation, validation results, observations and the decisions that depend on them.</strong></div>
        </div>
        <div className="prohibition-strip"><span>DETERMINISTIC COMPUTATION</span><span>PHYSICAL OBSERVATIONS</span><span>STRUCTURED TOOLS</span><span>TRACEABLE RESULTS</span></div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head">
          <div><span>THE TECHNOLOGY</span><h2>Multiple engineering systems work together.</h2></div>
          <p>Fabrient combines deterministic algorithms, physics-based methods, machine learning and computer vision where each approach is useful. The engineering workflow keeps their outputs tied to the underlying product and physical data.</p>
        </div>
        <div className="intelligence-stack">
          <div><span>01</span><strong>Algorithms</strong><p>Geometry, tolerances, constraints and repeatable engineering calculations provide consistent results.</p></div>
          <div><span>02</span><strong>Physics</strong><p>Physical models help evaluate behavior that depends on forces, materials, motion and manufacturing conditions.</p></div>
          <div><span>03</span><strong>Machine Learning</strong><p>Learn useful patterns from engineering and production data when a learned model adds information beyond deterministic computation.</p></div>
          <div><span>04</span><strong>Computer Vision</strong><p>Extract physical information from images and inspection workflows and connect observations to the corresponding product state.</p></div>
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head">
          <div><span>SIM-TO-REAL</span><h2>Use physical results to improve the next engineering cycle.</h2></div>
          <p>The useful dataset is created when predictions, builds and measurements remain connected. Fabrient is designed to preserve that history so each completed cycle can contribute to better engineering decisions.</p>
        </div>
        <div className="reality-flow">
          <div><small>01</small><strong>Predict</strong><p>Calculate the expected engineering result.</p></div>
          <i>→</i>
          <div><small>02</small><strong>Produce</strong><p>Build the physical product.</p></div>
          <i>→</i>
          <div><small>03</small><strong>Observe</strong><p>Capture measurements and visual evidence.</p></div>
          <i>→</i>
          <div><small>04</small><strong>Calibrate</strong><p>Feed useful observations into future decisions.</p></div>
        </div>
      </section>

      <section id="pricing" className="cad-work pricing-section">
        <div className="cad-section-head">
          <div><span>PLANS THAT MATCH THE WORK</span><h2>Start with the tools your team needs.</h2></div>
          <p>Free gives you a practical starting point. Hobby gives an individual builder the full personal workflow. Startup adds team execution. Enterprise provides organization-wide control and support.</p>
        </div>
        <div className="pricing-grid">
          {PLAN_ORDER.map((key) => {
            const plan = FABRINAT_PLANS[key]
            const enterprise = key === 'enterprise'
            return (
              <article className={`pricing-card${key === 'startup' ? ' featured' : ''}`} key={key}>
                <div className="pricing-card-head"><span>{plan.name.toUpperCase()}</span><strong>{enterprise ? 'Contact' : plan.price === 0 ? 'Free' : `$${plan.price}`} </strong>{!enterprise && (plan.price ?? 0) > 0 && <small>/ month</small>}</div>
                <p className="pricing-audience">{plan.audience} · {plan.teamSize}</p>
                <h3>{plan.tagline}</h3>
                <p className="pricing-usage"><strong>{planUsageLabel(key)}</strong><br />{plan.limits.projects === -1 ? 'Unlimited projects' : `${plan.limits.projects} project${plan.limits.projects === 1 ? '' : 's'}`} · {plan.limits.storageGb === -1 ? 'Unlimited storage' : `${plan.limits.storageGb} GB storage`}</p>
                <ul>{plan.highlights.map((highlight) => <li key={highlight}>{highlight}</li>)}</ul>
                <div className="pricing-contact-actions"><a className="cad-button" href={`mailto:${CONTACT_EMAIL}?subject=Fabrient%20${encodeURIComponent(plan.name)}%20plan`}>EMAIL FABRIENT</a><a className="cad-button" href={`tel:${CONTACT_PHONE}`}>CALL FABRIENT</a></div>
              </article>
            )
          })}
        </div>
      </section>

      <section className="cad-work final-cta-section">
        <div><span>EARLY ENGINEERING TEAMS</span><h2>Bring us a difficult sim-to-real problem.</h2><p>Tell us about the product, the engineering workflow and the physical result you need to understand. We are interested in problems where better connection between design data and production evidence can change the outcome.</p></div>
        <div className="cad-actions"><a href={`mailto:${CONTACT_EMAIL}?subject=Fabrient%20sim-to-real%20problem`} className="cad-button cad-button-main">EMAIL FABRIENT <span>→</span></a><a href={`tel:${CONTACT_PHONE}`} className="cad-button">CALL FABRIENT <span>→</span></a></div>
      </section>

      <footer className="presale-footer"><strong>FABRIENT</strong><div><a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a><a href={`tel:${CONTACT_PHONE}`}>{CONTACT_PHONE}</a></div></footer>
    </main>
  )
}

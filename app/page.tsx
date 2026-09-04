import Image from 'next/image'
import Link from 'next/link'
import { ENTERPRISE_CONTACT, FABRINAT_PLANS, planUsageLabel } from '@/lib/fabrinat-plans'

const PLAN_ORDER = ['free', 'hobbyist', 'startup', 'enterprise'] as const
const CONTACT_EMAIL = ENTERPRISE_CONTACT.email
const CONTACT_PHONE = ENTERPRISE_CONTACT.phone
const REAL_PHOTO = 'https://images.pexels.com/photos/22491107/pexels-photo-22491107.jpeg?auto=compress&cs=tinysrgb&w=1600'
const DEMO_VIDEO_URL = 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663321590917/uilhFdzHJgyMSihq.mp4'

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
          <h1>Design it. Build it. Learn from it.</h1>
          <p>Fabrient connects engineering work to what happens on the factory floor.</p>
          <div className="cad-actions">
            <a href={`mailto:${CONTACT_EMAIL}?subject=Fabrient%20presale`} className="cad-button cad-button-main">TALK TO US <span>→</span></a>
            <a href="#solution" className="cad-button">SEE THE LOOP</a>
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
          <div><span>FABRIENT IN ACTION</span><h2 id="launch-demo-title">See it in action.</h2></div>
          <p>Two minutes. One connected engineering loop.</p>
        </div>
        <div className="launch-demo-frame">
          <iframe
            src={DEMO_VIDEO_URL}
            title="Fabrient launch demo"
            loading="eager"
            allow="autoplay; fullscreen; picture-in-picture"
            allowFullScreen
          />
          <a className="launch-demo-link" href={DEMO_VIDEO_URL} target="_blank" rel="noreferrer">VIDEO NOT PLAYING? OPEN THE DEMO ↗</a>
        </div>
      </section>

      <section id="problem" className="cad-work technical-section">
        <div className="cad-section-head">
          <div><span>THE PROBLEM</span><h2>Design files do not tell the whole story.</h2></div>
          <p>Real builds create real data. Keep it connected to the decisions behind the part.</p>
        </div>
        <div className="reality-flow three-d-rail">
          <div><small>01</small><strong>Design</strong><p>Set geometry and intent.</p></div><i>→</i>
          <div><small>02</small><strong>Build</strong><p>Make the physical part.</p></div><i>→</i>
          <div><small>03</small><strong>Measure</strong><p>Capture what changed.</p></div><i>→</i>
          <div><small>04</small><strong>Improve</strong><p>Make the next call better.</p></div>
        </div>
      </section>

      <section id="solution" className="cad-work technical-section">
        <div className="cad-section-head">
          <div><span>THE SOLUTION</span><h2>One loop from design to proof.</h2></div>
          <p>Connect computation, production and measurement to every revision.</p>
        </div>
        <div className="solution-constellation">
          <div className="solution-cube" aria-label="Connected engineering loop">
            <div className="cube-face cube-face-front"><span>DEFINE</span><h3>Set the baseline.</h3><p>Capture geometry, constraints and intent.</p></div>
            <div className="cube-face cube-face-right"><span>MEASURE</span><h3>Bring reality back in.</h3><p>Keep inspection and production data with the part.</p></div>
            <div className="cube-face cube-face-top"><span>IMPROVE</span><h3>Make the next call better.</h3><p>Compare expected and measured results.</p></div>
            <div className="cube-core">SIM <b>↔</b> REAL<small>CONNECTED LOOP</small></div>
          </div>
        </div>
      </section>

      <section id="mcp" className="cad-work technical-section mcp-section">
        <div className="cad-section-head">
          <div><span>FOR AI AGENTS</span><h2>Give agents tools they can trust.</h2></div>
          <p>Authenticated operations. Structured results. Engineering context.</p>
        </div>
        <div className="agent-constellation">
          <div className="agent-cube" aria-label="Trusted agent tools">
            <div className="cube-face agent-face-front"><span>AGENT</span><strong>Reads the engineering task and selects the required operation.</strong></div>
            <div className="cube-face agent-face-right"><span>FABRIENT MCP</span><strong>Executes authenticated tools and returns structured engineering results.</strong></div>
            <div className="cube-face agent-face-top"><span>ENGINEERING STATE</span><strong>Stores computation, validation results, observations and the decisions that depend on them.</strong></div>
            <div className="cube-core">MCP <b>↕</b><small>TRUSTED TOOLS</small></div>
          </div>
        </div>
        <div className="prohibition-strip"><span>DETERMINISTIC COMPUTATION</span><span>PHYSICAL OBSERVATIONS</span><span>STRUCTURED TOOLS</span><span>TRACEABLE RESULTS</span></div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head">
          <div><span>THE TECHNOLOGY</span><h2>Use the right tool for the job.</h2></div>
          <p>Algorithms, physics, ML and vision—connected to the product.</p>
        </div>
        <div className="technology-constellation">
          <div><span>01</span><strong>Algorithms</strong><p>Repeatable engineering math.</p></div>
          <div><span>02</span><strong>Physics</strong><p>Models for real behavior.</p></div>
          <div><span>03</span><strong>Machine Learning</strong><p>Patterns in your production data.</p></div>
          <div><span>04</span><strong>Computer Vision</strong><p>Measurements from images.</p></div>
        </div>
      </section>

      <section className="cad-work technical-section">
        <div className="cad-section-head">
          <div><span>SIM-TO-REAL</span><h2>Every build makes the next one smarter.</h2></div>
          <p>Predict. Produce. Observe. Calibrate.</p>
        </div>
        <div className="reality-flow three-d-rail">
          <div><small>01</small><strong>Predict</strong><p>Know what to expect.</p></div>
          <i>→</i>
          <div><small>02</small><strong>Produce</strong><p>Make the part.</p></div>
          <i>→</i>
          <div><small>03</small><strong>Observe</strong><p>See what happened.</p></div>
          <i>→</i>
          <div><small>04</small><strong>Calibrate</strong><p>Improve the next run.</p></div>
        </div>
      </section>

      <section id="pricing" className="cad-work pricing-section">
        <div className="cad-section-head">
          <div><span>PLANS</span><h2>Start where you are.</h2></div>
          <p>Choose the workflow that fits your team.</p>
        </div>
        <div className="pricing-constellation">
          {PLAN_ORDER.map((key) => {
            const plan = FABRINAT_PLANS[key]
            const enterprise = key === 'enterprise'
            return (
              <article className={`pricing-node${key === 'startup' ? ' featured' : ''}`} key={key}>
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
        <div><span>EARLY ENGINEERING TEAMS</span><h2>Have a hard physical problem?</h2><p>Let’s solve it.</p></div>
        <div className="cad-actions"><a href={`mailto:${CONTACT_EMAIL}?subject=Fabrient%20sim-to-real%20problem`} className="cad-button cad-button-main">EMAIL FABRIENT <span>→</span></a><a href={`tel:${CONTACT_PHONE}`} className="cad-button">CALL FABRIENT <span>→</span></a></div>
      </section>

      <footer className="presale-footer"><strong>FABRIENT</strong><div><a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a><a href={`tel:${CONTACT_PHONE}`}>{CONTACT_PHONE}</a></div></footer>
    </main>
  )
}

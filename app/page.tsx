import Link from 'next/link'
import { ENTERPRISE_CONTACT, FABRINAT_PLANS, planUsageLabel } from '@/lib/fabrinat-plans'

const PLAN_ORDER = ['free', 'hobbyist', 'startup', 'enterprise'] as const
const CONTACT_EMAIL = ENTERPRISE_CONTACT.email
const CONTACT_PHONE = ENTERPRISE_CONTACT.phone

export default function Home() {
  return (
    <main className="cad-home presale-home">
      <header className="presale-nav">
        <Link href="/" className="brand">FABRIENT</Link>
        <nav aria-label="Main navigation">
          <a href="#problem">Problem</a><a href="#solution">Solution</a><a href="#mcp">MCP</a><a href="#pricing">Pricing</a><a href={`mailto:${CONTACT_EMAIL}`}>Contact</a>
        </nav>
      </header>
      <section className="cad-hero presale-hero">
        <div className="cad-intro">
          <div className="cad-kicker"><span className="live-dot" /> FABRIENT / SIM → REAL</div>
          <h1>Engineering software can simulate the product.<br /><em>It cannot build reality.</em></h1>
          <p>Fabrient is building the layer that connects engineering intent, deterministic checks, agents and real physical evidence — so what happens on the screen can be compared with what happens in the real world.</p>
          <div className="cad-actions"><a href={`mailto:${CONTACT_EMAIL}?subject=Fabrient%20presale`} className="cad-button cad-button-main">TALK TO US <span>→</span></a><a href={`tel:${CONTACT_PHONE}`} className="cad-button">CALL US <span>→</span></a><a href="#solution" className="cad-button">SEE HOW IT WORKS</a></div>
          <div className="friendly-note"><span className="live-dot" /> We are pre-selling the first narrow version. The full platform stays archived until customers prove what deserves to be built.</div>
        </div>
        <div className="presale-hero-visual" aria-hidden="true"><div className="sim-card"><span>DIGITAL</span><strong>SIMULATE</strong><small>expected result</small></div><div className="sim-arrow">→</div><div className="real-card"><span>PHYSICAL</span><strong>MEASURE</strong><small>observed result</small></div><div className="gap-label">THE GAP FABRIENT CLOSES</div></div>
      </section>
      <section id="problem" className="cad-work technical-section">
        <div className="cad-section-head"><div><span>THE PROBLEM</span><h2>Simulation is not reality.</h2></div><p>Physical products introduce manufacturing variation, fit issues, process behavior, measurement error and assumptions that were never tested.</p></div>
        <div className="reality-flow"><div><small>01</small><strong>Design</strong><p>A model predicts what should happen.</p></div><i>→</i><div><small>02</small><strong>Build</strong><p>The physical product introduces reality.</p></div><i>→</i><div><small>03</small><strong>Measure</strong><p>Actual observations reveal the difference.</p></div><i>→</i><div><small>04</small><strong>Learn</strong><p>Evidence improves the next decision.</p></div></div>
      </section>
      <section id="solution" className="cad-work technical-section">
        <div className="cad-section-head"><div><span>THE SOLUTION</span><h2>Close the loop between prediction and the part.</h2></div><p>Fabrient coordinates the engineering job, runs repeatable checks, records what was predicted, brings back physical observations and makes the gap visible.</p></div>
        <div className="capability-grid presale-grid"><article><span>BEFORE THE BUILD</span><h3>Establish the engineering baseline.</h3><p>Use deterministic geometry, dimensions, constraints and manufacturing checks to establish what the system says should happen.</p></article><article><span>AFTER THE BUILD</span><h3>Bring back evidence.</h3><p>Measurements, inspection results and physical observations stay separate from assumptions and model output.</p></article><article><span>ACROSS REVISIONS</span><h3>Compare prediction with reality.</h3><p>See where the digital expectation and physical result disagree, then use supported observations to improve the next decision.</p></article></div>
      </section>
      <section id="mcp" className="cad-work technical-section mcp-section">
        <div className="cad-section-head"><div><span>FOR AI AGENTS</span><h2>MCP gives agents access to the engineering layer.</h2></div><p>The point of MCP is not another chatbot. It gives an agent structured access to bounded engineering operations while keeping engineering evidence authoritative.</p></div>
        <div className="agent-story"><div className="agent-node"><span>AGENT</span><strong>Understands the job and decides what bounded action is needed.</strong></div><div className="agent-arrow">↓</div><div className="agent-node"><span>FABRIENT MCP</span><strong>Runs authenticated engineering tools and returns structured results, units, validation state and blockers.</strong></div><div className="agent-arrow">↓</div><div className="agent-node"><span>ENGINEERING EVIDENCE</span><strong>Deterministic computation and real observations decide what is true. Missing evidence remains a blocker.</strong></div></div>
        <div className="prohibition-strip"><span>DETERMINISTIC CHECKS</span><span>REAL OBSERVATIONS</span><span>BOUNDED ACTIONS</span><span>TRACEABLE EVIDENCE</span></div>
      </section>
      <section className="cad-work technical-section">
        <div className="cad-section-head"><div><span>WHY FABRIENT</span><h2>Not another AI wrapper around engineering software.</h2></div></div>
        <div className="intelligence-stack"><div><span>01</span><strong>Reality stays separate</strong><p>A simulation or model does not become physical evidence just because an AI produced it.</p></div><div><span>02</span><strong>Engineering stays deterministic</strong><p>Where a repeatable calculation is possible, the engineering layer—not the language model—owns the answer.</p></div><div><span>03</span><strong>Agents get structure</strong><p>MCP exposes engineering capabilities as bounded tools instead of forcing agents to scrape a UI or invent their own workflow.</p></div><div><span>04</span><strong>Evidence compounds</strong><p>Prediction, build results and measurements can stay connected across revisions so the system can learn from reality.</p></div></div>
      </section>
      <section id="pricing" className="cad-work pricing-section">
        <div className="cad-section-head"><div><span>PLANS THAT MATCH THE WORK</span><h2>Start small. Add the control you need.</h2></div><p>Every plan keeps the engineering state and evidence visible. Free is useful on purpose, Hobby gives one builder every individual feature, Startup adds team execution, and Enterprise adds organization-wide control.</p></div>
        <div className="pricing-grid">
          {PLAN_ORDER.map((key) => {
            const plan = FABRINAT_PLANS[key]
            const enterprise = key === 'enterprise'
            return (
              <article className={`pricing-card${key === 'startup' ? ' featured' : ''}`} key={key}>
                <div className="pricing-card-head"><span>{plan.name.toUpperCase()}</span><strong>{enterprise ? 'Contact' : plan.price === 0 ? 'Free' : `$${plan.price ?? 0}`} </strong>{!enterprise && (plan.price ?? 0) > 0 && <small>/ month</small>}</div>
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
      <section className="cad-work final-cta-section"><div><span>WE ARE TALKING TO EARLY USERS NOW</span><h2>Have a real sim-to-real problem?<br /><em>Show us the gap.</em></h2><p>We want the ugly cases: where the simulation looked right, the build did not, and you need to understand why.</p></div><div className="cad-actions"><a href={`mailto:${CONTACT_EMAIL}?subject=Fabrient%20sim-to-real%20problem`} className="cad-button cad-button-main">EMAIL FABRIENT <span>→</span></a><a href={`tel:${CONTACT_PHONE}`} className="cad-button">CALL FABRIENT <span>→</span></a></div></section>
      <footer className="presale-footer"><strong>FABRIENT</strong><div><a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a><a href={`tel:${CONTACT_PHONE}`}>{CONTACT_PHONE}</a></div></footer>
    </main>
  )
}

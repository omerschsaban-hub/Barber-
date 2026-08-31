import Link from 'next/link';
import FabrientMark from './fabrient-mark';

/**
 * Keep the global shell server-rendered and dependency-free.
 * Authentication belongs on routes that actually need it; the global
 * navigation must always be renderable.
 */
export default function AppHeader() {
  return (
    <header className="topbar">
      <FabrientMark />
      <nav>
        <Link href="/workspace">Workspace</Link>
        <Link href="/projects">Projects</Link>
        <Link href="/manufacturing">Build</Link>
        <Link href="/import">Inspect</Link>
      </nav>
      <div className="nav-secondary">
        <Link href="/geometry">Geometry</Link>
        <Link href="/calibration">Calibration</Link>
        <Link href="/graph">Evidence</Link>
        <Link href="/records">Exports</Link>
        <Link href="/integrations">Integrations</Link>
        <Link href="/changelog">Changelog</Link>
      </div>
      <div>
        <Link href="/login" className="button">Sign in</Link>
      </div>
    </header>
  );
}

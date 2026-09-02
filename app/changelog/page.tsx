import Link from 'next/link';
import Breadcrumbs from '@/components/breadcrumbs';
import { changelog, changelogKindLabel } from '@/lib/changelog';
import './changelog.css';

export const metadata = {
  title: 'Changelog',
  description: 'Product updates, fixes, and engineering improvements shipped in Fabrient.',
  alternates: { canonical: '/changelog' },
};

export default function ChangelogPage() {
  return (
    <main className="changelog-page">
      <section className="changelog-hero">
        <Breadcrumbs items={[{ label: 'Fabrient', href: '/' }, { label: 'Changelog' }]} />
        <p className="changelog-eyebrow">Fabrient updates</p>
        <h1>What’s new</h1>
        <p className="changelog-intro">
          Product changes, fixes, and improvements worth knowing about. No raw commit noise.
        </p>
        <Link href="/workspace" className="changelog-back">Back to workspace</Link>
      </section>

      <section className="changelog-list" aria-label="Release history">
        {changelog.map((release) => (
          <article className="release" key={release.version}>
            <div className="release-meta">
              <span className="release-version">{release.version}</span>
              <time dateTime={release.date}>
                {new Date(`${release.date}T00:00:00Z`).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                  timeZone: 'UTC',
                })}
              </time>
            </div>
            <div className="release-content">
              <h2>{release.title}</h2>
              <ul>
                {release.items.map((item, index) => (
                  <li key={`${release.version}-${item.kind}-${index}`}>
                    <span className={`change-badge change-${item.kind}`}>
                      {changelogKindLabel[item.kind]}
                    </span>
                    <span>{item.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

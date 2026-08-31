import Link from 'next/link';
import { changelog, changelogKindLabel } from '@/lib/changelog';
import './changelog.css';

export const metadata = {
  title: 'Changelog — Fabrient',
  description: 'Product updates, improvements, fixes, and important changes in Fabrient.',
};

export default function ChangelogPage() {
  return (
    <main className="changelog-page">
      <section className="changelog-hero">
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

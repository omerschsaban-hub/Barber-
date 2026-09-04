import './globals.css';
import './cad-home.css';
import './fabrient-ux.css';
import './fabrient-start.css';
import './fabrinat-design.css';
import './fabrient-landing.css';
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/next';

const PUBLIC_WEB_URL = process.env.NEXT_PUBLIC_FABRIENT_WEB_URL || 'https://fabrinat-omega.vercel.app';

export const metadata = {
  metadataBase: new URL(PUBLIC_WEB_URL),
  title: {
    default: 'Fabrient — From intent to something real',
    template: '%s — Fabrient',
  },
  description: 'Fabrient connects physical-product intent, CAD, deterministic engineering, build preparation, measurement, learning and release evidence.',
  alternates: { canonical: '/' },
  robots: { index: true, follow: true },
  icons: { icon: '/icon.svg', shortcut: '/icon.svg' },
  openGraph: {
    title: 'Fabrient — From intent to something real',
    description: 'One engineering journey from intent to build and proof.',
    url: PUBLIC_WEB_URL,
    siteName: 'Fabrient',
    type: 'website',
    images: [{ url: '/opengraph-image', width: 1200, height: 630, alt: 'Fabrient — From intent to something real' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Fabrient — From intent to something real',
    description: 'Physical engineering from design to proof.',
    images: ['/twitter-image'],
  },
};

const structuredData = {
  '@context': 'https://schema.org',
  '@graph': [
    {
      '@type': 'Organization',
      name: 'Fabrient',
      url: PUBLIC_WEB_URL,
      logo: `${PUBLIC_WEB_URL}/icon.svg`,
    },
    {
      '@type': 'WebSite',
      name: 'Fabrient',
      url: PUBLIC_WEB_URL,
      description: 'Physical-product engineering from intent to release.',
    },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" style={{ backgroundColor: '#f3f0e8', color: '#172019' }}>
      <body style={{ backgroundColor: '#f3f0e8', color: '#172019' }}>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }} />
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}

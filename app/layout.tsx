import './globals.css';
import './cad-home.css';
import './fabrient-ux.css';
import './fabrient-start.css';
import './fabrinat-design.css';
import './fabrient-landing.css';
import AppHeader from '@/components/app-header';
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/next';

export const metadata = {
  metadataBase: new URL('https://getfabrient.com'),
  title: 'Fabrient — From intent to something real',
  description: 'Fabrient brings physical-product work together from intent and CAD through engineering, manufacturing, measurement, learning and release.',
  alternates: { canonical: '/' },
  openGraph: {
    title: 'Fabrient — From intent to something real',
    description: 'One engineering journey from intent to build and proof.',
    url: 'https://getfabrient.com',
    siteName: 'Fabrient',
    type: 'website'
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" style={{ backgroundColor: '#f3f0e8', color: '#172019' }}>
      <body style={{ backgroundColor: '#f3f0e8', color: '#172019' }}>
        <AppHeader />
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}

import './globals.css';
import './cad-home.css';
import './fabrient-ux.css';
import './fabrient-start.css';
import './fabrinat-design.css';
import AppHeader from '@/components/app-header';
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/next';

export const metadata = {
  metadataBase: new URL('https://getfabrient.com'),
  title: 'Fabrient — Engineering System for Physical Products',
  description: 'Turn bounded physical-engineering jobs into verified outcomes with deterministic computation, CAD/DFM validation, real measurement, machine learning and auditable manufacturing release.',
  alternates: { canonical: '/' },
  openGraph: {
    title: 'Fabrient — Engineering System for Physical Products',
    description: 'Deterministic engineering, real evidence and bounded agents from intent to manufacturing release.',
    url: 'https://getfabrient.com',
    siteName: 'Fabrient',
    type: 'website'
  }
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppHeader />
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}

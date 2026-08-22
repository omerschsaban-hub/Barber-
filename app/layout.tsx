import './globals.css';
import './cad-home.css';
import './fabrient-ux.css';
import './fabrient-start.css';
import './fabrinat-design.css';
import AppHeader from '@/components/app-header';
import { Analytics } from '@vercel/analytics/react';
import { SpeedInsights } from '@vercel/speed-insights/next';

export const metadata = {
  title: 'Fabrient — Engineering Release System',
  description: 'From part definition to verified manufacturing release.'
};

/**
 * Keep the root document deterministic and dependency-light.
 *
 * Analytics/SpeedInsights are intentionally not mounted in the root shell:
 * they are client components and add post-hydration JavaScript to every route.
 * A production shell must be able to render even when an optional telemetry
 * bundle is unavailable or fails. Telemetry can be mounted in a dedicated
 * client-safe provider later without making the entire application depend on it.
 */
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

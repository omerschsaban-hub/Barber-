import './globals.css';
import './cad-home.css';
import './fabrient-ux.css';
import './fabrient-start.css';
import AppHeader from '@/components/app-header';
import { SpeedInsights } from '@vercel/speed-insights/next';

export const metadata = {
  title: 'Fabrient — Engineering Release System',
  description: 'From part definition to verified manufacturing release.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppHeader />
        {children}
        <SpeedInsights />
      </body>
    </html>
  );
}

import './globals.css';
import './cad-home.css';
import './fabrient-ux.css';
import AppHeader from '@/components/app-header';

export const metadata = {
  title: 'Fabrient — Engineering Release System',
  description: 'From part definition to verified manufacturing release.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="fabrient-splash" aria-hidden="true">
          <div className="fabrient-splash-inner">
            <div className="fabrient-splash-mark">F</div>
            <div className="fabrient-splash-name">FABRIENT</div>
            <div className="fabrient-splash-sub">ENGINEERING RELEASE SYSTEM</div>
          </div>
        </div>
        <AppHeader />
        {children}
      </body>
    </html>
  );
}

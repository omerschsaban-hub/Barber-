import './globals.css';
import './cad-home.css';
import AppHeader from '@/components/app-header';

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
      </body>
    </html>
  );
}

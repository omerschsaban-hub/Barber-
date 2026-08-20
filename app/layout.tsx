import './globals.css';
import './fabrient-effects.css';
import EngineeringLoopTracker from '@/components/engineering-loop-tracker';
import AppHeader from '@/components/app-header';

export const metadata = {
  title: 'Fabrient — Engineering Release System',
  description: 'From part definition to verified manufacturing release.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <EngineeringLoopTracker />
        <AppHeader />
        {children}
      </body>
    </html>
  );
}

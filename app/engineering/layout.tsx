import EngineeringCopilot from './EngineeringCopilot';

export default function EngineeringLayout({children}: {children: React.ReactNode}) {
  return <>
    <EngineeringCopilot />
    {children}
  </>;
}

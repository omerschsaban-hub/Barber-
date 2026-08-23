import Link from 'next/link';

export default function FabrientMark({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" className={`fabrient-mark${compact ? ' fabrient-mark-compact' : ''}`} aria-label="Fabrient home">
      <span className="fabrient-mark-symbol" aria-hidden="true">
        <span className="fabrient-mark-frame" />
        <span className="fabrient-mark-axis fabrient-mark-axis-x" />
        <span className="fabrient-mark-axis fabrient-mark-axis-y" />
        <span className="fabrient-mark-core" />
      </span>
      <span className="fabrient-mark-word">FABRIENT</span>
    </Link>
  );
}

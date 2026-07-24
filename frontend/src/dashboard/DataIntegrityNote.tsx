import { Contribution } from './types';
import { mono } from './styles';

interface DataIntegrityNoteProps {
  contributions: Contribution[];
}

export default function DataIntegrityNote({ contributions }: DataIntegrityNoteProps) {
  const resolved = contributions.filter((c) => c.mp_id !== null).length;
  const rate =
    contributions.length > 0 ? Math.round((resolved / contributions.length) * 1000) / 10 : 0;

  return (
    <div
      style={{
        padding: 12,
        background: 'var(--bg-surface)',
        borderLeft: '3px solid var(--accent-amber)',
      }}
    >
      <span
        style={{
          ...mono,
          fontSize: 9,
          color: 'var(--accent-amber)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
        }}
      >
        Data Integrity
      </span>
      <p style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 4, lineHeight: 1.5, marginBottom: 0 }}>
        {rate}% of records were automatically matched to the correct MP. Names we could not match
        are shown as unmatched — we never guess.
      </p>
    </div>
  );
}

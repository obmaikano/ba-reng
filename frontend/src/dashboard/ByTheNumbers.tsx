import { Contribution } from './types';
import { narrativeSection, sectionTitle, mono, surface, statRow, statRowLast } from './styles';

interface ByTheNumbersProps {
  contributions: Contribution[];
}

const TYPE_LABELS: Record<string, string> = {
  question: 'Questions asked',
  oral_question: 'Questions asked',
  motion: 'Motions moved',
  bill_presentation: 'Bill readings',
  bill_1st: 'Bill readings',
  bill_2nd: 'Bill readings',
  bill_3rd: 'Bill readings',
  minist_question: "Minister's Question Time",
};

export default function ByTheNumbers({ contributions }: ByTheNumbersProps) {
  const counts = new Map<string, string>();
  for (const c of contributions) {
    const key = TYPE_LABELS[c.contribution_type] ?? c.contribution_type;
    counts.set(key, String((Number(counts.get(key)) || 0) + 1));
  }

  const ministriesAddressed = new Set(
    contributions.map((c) => c.ministry_addressed).filter((m): m is string => Boolean(m)),
  ).size;

  const rows: { label: string; count: string; color?: string }[] = [
    { label: 'Questions asked', count: counts.get('Questions asked') ?? '0' },
    { label: 'Motions moved', count: counts.get('Motions moved') ?? '0' },
    { label: 'Bill readings', count: counts.get('Bill readings') ?? '0' },
    { label: "Minister's Question Time", count: counts.get("Minister's Question Time") ?? '0' },
    { label: 'Ministries addressed', count: String(ministriesAddressed) },
  ];

  return (
    <div style={narrativeSection}>
      <div style={{ ...sectionTitle, display: 'flex', alignItems: 'center', gap: 4 }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        BY THE NUMBERS
      </div>
      <div style={{ ...surface, padding: 16 }}>
        {rows.map((row, index) => {
          const style = index === rows.length - 1 ? statRowLast : statRow;
          return (
            <div key={row.label} style={style}>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{row.label}</span>
              <span style={{ ...mono, fontSize: 12, color: row.color ?? 'var(--accent-blue)' }}>
                {row.count}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

import { Contribution } from './types';
import { card, sectionTitle, mono } from './styles';

interface ByTheNumbersProps {
  contributions: Contribution[];
}

const TYPE_LABELS: Record<string, string> = {
  question: 'Questions asked',
  oral_question: 'Questions asked',
  motion: 'Motions moved',
  bill_presentation: 'Bills presented',
  tabling: 'Papers tabled',
  amendment: 'Amendments',
};

function friendlyLabel(type: string): string {
  return TYPE_LABELS[type] ?? type.replace(/_/g, ' ').replace(/^\w/, (ch) => ch.toUpperCase());
}

export default function ByTheNumbers({ contributions }: ByTheNumbersProps) {
  const counts = new Map<string, number>();
  for (const c of contributions) {
    counts.set(c.contribution_type, (counts.get(c.contribution_type) ?? 0) + 1);
  }
  const rows = Array.from(counts.entries())
    .map(([type, count]) => ({ label: friendlyLabel(type), count }))
    .sort((a, b) => b.count - a.count);

  const ministriesAddressed = new Set(
    contributions.map((c) => c.ministry_addressed).filter((m): m is string => Boolean(m)),
  ).size;
  rows.push({ label: 'Ministries addressed', count: ministriesAddressed });

  return (
    <div style={card}>
      <div style={sectionTitle}>By The Numbers</div>
      <div>
        {rows.map((row, index) => (
          <div
            key={row.label}
            style={{
              display: 'flex',
              alignItems: 'baseline',
              justifyContent: 'space-between',
              padding: '6px 0',
              borderBottom: index === rows.length - 1 ? 'none' : '1px solid var(--border-subtle)',
            }}
          >
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{row.label}</span>
            <span style={{ ...mono, fontSize: 12, color: 'var(--accent-blue)' }}>{row.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

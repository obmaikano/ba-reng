import { Contribution } from './types';
import { card, sectionTitle, mono } from './styles';

interface ByTheNumbersProps {
  contributions: Contribution[];
}

export default function ByTheNumbers({ contributions }: ByTheNumbersProps) {
  const counts = new Map<string, number>();
  for (const c of contributions) {
    counts.set(c.contribution_type, (counts.get(c.contribution_type) ?? 0) + 1);
  }
  const rows = Array.from(counts.entries()).sort(([, a], [, b]) => b - a);
  const ministriesAddressed = new Set(
    contributions.map((c) => c.ministry_addressed).filter((m): m is string => Boolean(m)),
  ).size;

  return (
    <div style={card}>
      <div style={sectionTitle}>By The Numbers</div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <tbody>
          {rows.map(([type, count]) => (
            <tr key={type} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              <td style={{ padding: '6px 0', fontSize: 13, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                {type.replace(/_/g, ' ')}
              </td>
              <td style={{ ...mono, padding: '6px 0', fontSize: 13, color: 'var(--text-primary)', textAlign: 'right' }}>
                {count}
              </td>
            </tr>
          ))}
          <tr>
            <td style={{ padding: '6px 0', fontSize: 13, color: 'var(--text-secondary)' }}>
              Ministries addressed
            </td>
            <td style={{ ...mono, padding: '6px 0', fontSize: 13, color: 'var(--text-primary)', textAlign: 'right' }}>
              {ministriesAddressed}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

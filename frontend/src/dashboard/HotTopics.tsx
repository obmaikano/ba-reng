import { Contribution } from './types';
import { card, sectionTitle, mono } from './styles';

interface HotTopicsProps {
  contributions: Contribution[];
}

export default function HotTopics({ contributions }: HotTopicsProps) {
  const counts = new Map<string, number>();
  for (const c of contributions) {
    if (!c.ministry_addressed) continue;
    counts.set(c.ministry_addressed, (counts.get(c.ministry_addressed) ?? 0) + 1);
  }
  const topics = Array.from(counts.entries())
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  return (
    <div style={card}>
      <div style={sectionTitle}>Hot Topics</div>
      {topics.length === 0 ? (
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>No ministries recorded.</span>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {topics.map(([ministry, count]) => (
            <span
              key={ministry}
              style={{
                ...mono,
                fontSize: 11,
                color: 'var(--text-secondary)',
                border: '1px solid var(--border-default)',
                padding: '4px 8px',
              }}
            >
              {ministry} <span style={{ color: 'var(--accent-blue)' }}>{count}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

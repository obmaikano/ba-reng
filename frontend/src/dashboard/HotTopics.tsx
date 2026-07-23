import { Contribution } from './types';
import { card, sectionTitle, mono, ACCENT_ROTATION } from './styles';

interface HotTopicsProps {
  contributions: Contribution[];
}

interface Topic {
  ministry: string;
  count: number;
  mpNames: string[];
}

function topTopics(contributions: Contribution[]): Topic[] {
  const byMinistry = new Map<string, Contribution[]>();
  for (const c of contributions) {
    if (!c.ministry_addressed) continue;
    const bucket = byMinistry.get(c.ministry_addressed) ?? [];
    bucket.push(c);
    byMinistry.set(c.ministry_addressed, bucket);
  }

  return Array.from(byMinistry.entries())
    .map(([ministry, items]) => ({
      ministry,
      count: items.length,
      mpNames: Array.from(new Set(items.map((c) => c.mp_name).filter((n): n is string => Boolean(n)))).slice(0, 3),
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
}

export default function HotTopics({ contributions }: HotTopicsProps) {
  const topics = topTopics(contributions);

  return (
    <div style={card}>
      <div style={sectionTitle}>Hot Topics This Week</div>
      {topics.length === 0 ? (
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>No ministries recorded.</span>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {topics.map((topic, index) => {
            const accent = ACCENT_ROTATION[index % ACCENT_ROTATION.length];
            return (
              <div
                key={topic.ministry}
                style={{
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderLeft: `3px solid ${accent}`,
                  padding: '8px 10px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: accent }}>{topic.ministry}</span>
                  <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                    {topic.count} contribution{topic.count === 1 ? '' : 's'}
                  </span>
                </div>
                {topic.mpNames.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {topic.mpNames.map((name) => (
                      <span
                        key={name}
                        style={{
                          ...mono,
                          fontSize: 9,
                          color: 'var(--text-secondary)',
                          border: '1px solid var(--border-default)',
                          padding: '1px 6px',
                        }}
                      >
                        {name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

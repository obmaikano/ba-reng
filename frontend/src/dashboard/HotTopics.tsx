import { Contribution } from './types';
import { narrativeSection, sectionTitle, mono, ACCENT_ROTATION } from './styles';

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
    <div style={narrativeSection}>
      <div style={{ ...sectionTitle, display: 'flex', alignItems: 'center', gap: 4 }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>
        HOT TOPICS THIS WEEK
      </div>
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
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: 4,
                  }}
                >
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: accent,
                    }}
                  >
                    {topic.ministry}
                  </span>
                  <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                    {topic.count} question{topic.count === 1 ? '' : 's'}
                  </span>
                </div>
                {topic.mpNames.length > 0 && (
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {topic.mpNames.map((name) => (
                      <span
                        key={name}
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: 9,
                          color: 'var(--text-secondary)',
                          border: '1px solid var(--border-default)',
                          padding: '1px 6px',
                          textTransform: 'uppercase',
                          letterSpacing: '0.05em',
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

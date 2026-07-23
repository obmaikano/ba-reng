import { Contribution } from './types';
import { card, sectionTitle, mono } from './styles';

interface WeeklyTimelineProps {
  contributions: Contribution[];
}

export default function WeeklyTimeline({ contributions }: WeeklyTimelineProps) {
  const counts = new Map<string, number>();
  for (const c of contributions) {
    counts.set(c.date, (counts.get(c.date) ?? 0) + 1);
  }
  const days = Array.from(counts.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(-7);
  const maxCount = Math.max(1, ...days.map(([, count]) => count));

  return (
    <div style={card}>
      <div style={sectionTitle}>Weekly Timeline</div>
      {days.length === 0 ? (
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>No activity recorded.</span>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {days.map(([date, count]) => (
            <div key={date} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)', width: 80 }}>{date}</span>
              <div style={{ flex: 1, background: 'var(--bg-elevated)', height: 8 }}>
                <div
                  style={{
                    height: 8,
                    width: `${(count / maxCount) * 100}%`,
                    background: 'var(--accent-blue)',
                  }}
                />
              </div>
              <span style={{ ...mono, fontSize: 11, color: 'var(--text-secondary)', width: 24, textAlign: 'right' }}>
                {count}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

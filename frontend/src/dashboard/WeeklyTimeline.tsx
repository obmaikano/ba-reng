import { Contribution } from './types';
import { card, sectionTitle, mono, surfaceElevated, typeTag } from './styles';

interface WeeklyTimelineProps {
  contributions: Contribution[];
}

interface DaySummary {
  date: string;
  count: number;
  types: string[];
  ministries: string[];
}

const DAY_NAMES = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const MONTH_NAMES = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];

function formatDay(date: string): string {
  const d = new Date(date);
  return `${DAY_NAMES[d.getUTCDay()]} ${d.getUTCDate()} ${MONTH_NAMES[d.getUTCMonth()]}`;
}

function summarizeDays(contributions: Contribution[]): DaySummary[] {
  const byDate = new Map<string, Contribution[]>();
  for (const c of contributions) {
    const bucket = byDate.get(c.date) ?? [];
    bucket.push(c);
    byDate.set(c.date, bucket);
  }

  return Array.from(byDate.entries())
    .map(([date, items]) => ({
      date,
      count: items.length,
      types: Array.from(new Set(items.map((c) => c.contribution_type))),
      ministries: Array.from(
        new Set(items.map((c) => c.ministry_addressed).filter((m): m is string => Boolean(m))),
      ).slice(0, 3),
    }))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-7);
}

export default function WeeklyTimeline({ contributions }: WeeklyTimelineProps) {
  const days = summarizeDays(contributions);

  return (
    <div style={card}>
      <div style={sectionTitle}>This Week's Timeline</div>
      {days.length === 0 ? (
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>No activity recorded.</span>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {days.map((day) => (
            <div key={day.date} style={{ ...surfaceElevated, padding: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, flexWrap: 'wrap' }}>
                <span style={{ ...mono, fontSize: 10, color: 'var(--accent-blue)', fontWeight: 600 }}>
                  {formatDay(day.date)}
                </span>
                {day.types.map((type) => (
                  <span key={type} style={typeTag(type)}>{type}</span>
                ))}
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: 0 }}>
                {day.ministries.length > 0
                  ? `Ministries addressed: ${day.ministries.join(', ')}`
                  : 'No ministry recorded for these contributions.'}
              </p>
              <div style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', marginTop: 4 }}>
                {day.count} contribution{day.count === 1 ? '' : 's'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

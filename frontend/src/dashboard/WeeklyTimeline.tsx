import { Contribution } from './types';
import { narrativeSection, sectionTitle, mono, surfaceElevated, typeTag } from './styles';

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

function describeDay(day: DaySummary): string {
  if (day.ministries.length === 0) return 'No ministry recorded for these contributions.';
  return `${day.ministries.join(' and ')} addressed via ${day.types.map((t) => t.toUpperCase()).join(', ')}.`;
}

export default function WeeklyTimeline({ contributions }: WeeklyTimelineProps) {
  const days = summarizeDays(contributions);
  const sitting = days.filter((d) => d.count > 0);

  return (
    <div style={narrativeSection}>
      <div style={{ ...sectionTitle, display: 'flex', alignItems: 'center', gap: 4 }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        THIS WEEK'S TIMELINE
      </div>
      {sitting.length === 0 ? (
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>No activity recorded.</span>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {sitting.map((day) => (
            <div key={day.date} style={{ ...surfaceElevated, padding: 12 }}>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  marginBottom: 4,
                  flexWrap: 'wrap',
                }}
              >
                <span style={{ ...mono, fontSize: 10, color: 'var(--accent-blue)', fontWeight: 600 }}>
                  {formatDay(day.date)}
                </span>
                {day.types.map((type) => (
                  <span key={type} style={typeTag(type)}>{type.toUpperCase()}</span>
                ))}
              </div>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.4 }}>
                {describeDay(day)}
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

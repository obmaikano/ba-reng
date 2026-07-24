import { Contribution } from './types';
import { narrativeSection, statCard, grid4, statLabel, statValue, mono } from './styles';

interface WeekAtGlanceProps {
  contributions: Contribution[];
  activeMpCount: number;
  totalMpCount: number;
  prevWeekCount: number;
}

interface Stat {
  label: string;
  value: string;
  valueColor?: string;
  detail: string;
}

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function topMinistry(contributions: Contribution[]): { name: string; count: number } {
  const counts = new Map<string, number>();
  for (const c of contributions) {
    if (!c.ministry_addressed) continue;
    counts.set(c.ministry_addressed, (counts.get(c.ministry_addressed) ?? 0) + 1);
  }
  let name = '—';
  let count = 0;
  for (const [ministry, ministryCount] of counts) {
    if (ministryCount > count) {
      name = ministry;
      count = ministryCount;
    }
  }
  return { name, count };
}

function sittingDayNames(contributions: Contribution[]): string {
  const days = Array.from(new Set(contributions.map((c) => c.date)))
    .sort()
    .map((date) => DAY_NAMES[new Date(date).getUTCDay()]);
  return days.length > 0 ? Array.from(new Set(days)).join(', ') : '—';
}

function trendDetail(current: number, previous: number): string {
  const delta = current - previous;
  if (previous === 0) return 'vs prev week (none)';
  if (delta > 0) return `+${delta} vs prev week`;
  if (delta < 0) return `${delta} vs prev week`;
  return 'same as prev week';
}

export default function WeekAtGlance({
  contributions,
  activeMpCount,
  totalMpCount,
  prevWeekCount,
}: WeekAtGlanceProps) {
  const sittingDays = new Set(contributions.map((c) => c.date)).size;
  const ministry = topMinistry(contributions);

  const stats: Stat[] = [
    { label: 'Sitting Days', value: String(sittingDays), detail: sittingDayNames(contributions) },
    {
      label: 'Contributions',
      value: String(contributions.length),
      valueColor: 'var(--accent-blue)',
      detail: trendDetail(contributions.length, prevWeekCount),
    },
    {
      label: 'Active MPs',
      value: String(activeMpCount),
      valueColor: 'var(--accent-blue)',
      detail: `of ${totalMpCount} total`,
    },
    {
      label: 'Most Addressed',
      value: ministry.name,
      valueColor: 'var(--accent-amber)',
      detail: ministry.count > 0 ? `${ministry.count} question${ministry.count === 1 ? '' : 's'} this week` : 'No ministry recorded',
    },
  ];

  return (
    <div style={narrativeSection}>
      <div style={grid4}>
        {stats.map((stat) => (
          <div key={stat.label} style={statCard}>
            <div style={statLabel}>{stat.label}</div>
            <div
              style={{
                ...statValue,
                ...(stat.valueColor ? { color: stat.valueColor } : {}),
                fontSize: stat.value.length > 6 ? 16 : 20,
              }}
            >
              {stat.value}
            </div>
            <div style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', marginTop: 4 }}>
              {stat.detail}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

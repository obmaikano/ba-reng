import { Contribution, NarrativeData } from './types';
import { narrativeSection, statCard, grid4, statLabel, statValue, mono } from './styles';

interface WeekAtGlanceProps {
  contributions: Contribution[];
  activeMpCount: number;
  totalMpCount: number;
  prevWeekCount: number;
  narrative: NarrativeData | null;
}

interface Stat {
  label: string;
  value: string;
  valueColor?: string;
  detail: string;
}

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

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
  narrative,
}: WeekAtGlanceProps) {
  const sittingDays = new Set(contributions.map((c) => c.date)).size;

  const topMinistry = narrative?.summary_metrics?.top_addressed_ministry ?? '—';
  const topMinistryCount = narrative?.summary_metrics?.top_ministry_count ?? 0;
  const topMinistryPct = narrative?.summary_metrics?.top_ministry_pct ?? 0;

  const stats: Stat[] = [
    { label: 'Days Met', value: String(sittingDays), detail: sittingDayNames(contributions) },
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
      value: topMinistry,
      valueColor: 'var(--accent-amber)',
      detail: topMinistryCount > 0
        ? `${topMinistryCount} question${topMinistryCount === 1 ? '' : 's'} (${topMinistryPct}%)`
        : 'No ministry recorded',
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

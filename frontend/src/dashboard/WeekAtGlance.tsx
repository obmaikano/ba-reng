import { Contribution } from './types';
import { statCard, grid, statLabel, statValue } from './styles';

interface WeekAtGlanceProps {
  contributions: Contribution[];
  activeMpCount: number;
}

function topMinistry(contributions: Contribution[]): string {
  const counts = new Map<string, number>();
  for (const c of contributions) {
    if (!c.ministry_addressed) continue;
    counts.set(c.ministry_addressed, (counts.get(c.ministry_addressed) ?? 0) + 1);
  }
  let best = '—';
  let bestCount = 0;
  for (const [ministry, count] of counts) {
    if (count > bestCount) {
      best = ministry;
      bestCount = count;
    }
  }
  return best;
}

export default function WeekAtGlance({ contributions, activeMpCount }: WeekAtGlanceProps) {
  const activeDays = new Set(contributions.map((c) => c.date)).size;

  const stats = [
    { label: 'Active sitting days', value: String(activeDays) },
    { label: 'Recorded contributions', value: String(contributions.length) },
    { label: 'Active MPs', value: String(activeMpCount) },
    { label: 'Top ministry addressed', value: topMinistry(contributions) },
  ];

  return (
    <div style={grid}>
      {stats.map((stat) => (
        <div key={stat.label} style={statCard}>
          <div style={statLabel}>{stat.label}</div>
          <div style={statValue}>{stat.value}</div>
        </div>
      ))}
    </div>
  );
}

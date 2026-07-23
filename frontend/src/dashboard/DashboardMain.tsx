import { DashboardData } from './useDashboardData';
import WeekAtGlance from './WeekAtGlance';
import TopStory from './TopStory';
import WeeklyTimeline from './WeeklyTimeline';
import WhoWasActive from './WhoWasActive';
import ByTheNumbers from './ByTheNumbers';
import HotTopics from './HotTopics';
import RecentContributions from './RecentContributions';
import CaveatBanner from './CaveatBanner';

interface DashboardMainProps {
  data: DashboardData;
}

const DEFAULT_CAVEAT = 'Based on recorded contributions only. Not attendance data.';

export default function DashboardMain({ data }: DashboardMainProps) {
  const { weekContributions, weekStart, weekEnd, sittingDays, mps } = data;
  const activeMpCount = new Set(
    weekContributions.filter((c) => c.mp_id !== null).map((c) => c.mp_id),
  ).size;
  const caveat = mps[0]?.participation_index.caveat ?? DEFAULT_CAVEAT;
  const weekLabel = weekStart && weekEnd
    ? weekStart === weekEnd
      ? `Week of ${weekEnd}`
      : `Week of ${weekStart} – ${weekEnd}`
    : 'No sitting days recorded';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            color: 'var(--text-tertiary)',
            marginBottom: 4,
          }}
        >
          13th Parliament
        </div>
        <h1 style={{ color: 'var(--text-primary)', fontSize: 18, fontWeight: 600, margin: 0 }}>
          This Week in Parliament
        </h1>
        <p style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-tertiary)', marginTop: 4, fontSize: 11 }}>
          {weekLabel} · {sittingDays} sitting day{sittingDays === 1 ? '' : 's'} · {weekContributions.length} contributions · {activeMpCount} MPs active
        </p>
      </div>

      <WeekAtGlance contributions={weekContributions} activeMpCount={activeMpCount} />
      <TopStory contribution={weekContributions[0] ?? null} />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <WeeklyTimeline contributions={weekContributions} />
        <WhoWasActive contributions={weekContributions} mps={mps} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <ByTheNumbers contributions={weekContributions} />
        <HotTopics contributions={weekContributions} />
      </div>

      <RecentContributions contributions={weekContributions} />
      <CaveatBanner caveat={caveat} />
    </div>
  );
}

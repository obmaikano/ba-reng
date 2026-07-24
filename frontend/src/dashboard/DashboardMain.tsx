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

const MON_ABRV = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatDateRange(weekStart: string | null, weekEnd: string | null): string {
  if (!weekStart || !weekEnd) return 'No sitting days';
  const s = new Date(weekStart);
  const e = new Date(weekEnd);
  return `${e.getDate()}–${s.getDate()} ${MON_ABRV[s.getMonth()]} ${s.getFullYear()}`;
}

export default function DashboardMain({ data }: DashboardMainProps) {
  const { weekContributions, weekStart, weekEnd, sittingDays, prevWeekCount, mps, status } = data;
  const activeMpCount = new Set(
    weekContributions.filter((c) => c.mp_id !== null).map((c) => c.mp_id),
  ).size;

  const weekLabel = weekStart && weekEnd
    ? `Week of ${formatDateRange(weekStart, weekEnd)}`
    : 'Week of —';
  const subtitle = `${weekLabel} · ${sittingDays} sitting day${sittingDays === 1 ? '' : 's'} · ${weekContributions.length} contribution${weekContributions.length === 1 ? '' : 's'} · ${activeMpCount} MP${activeMpCount === 1 ? '' : 's'} active`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: 20,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--text-tertiary)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
              }}
            >
              13TH PARLIAMENT · 5TH SESSION
            </span>
            <span style={{ color: 'var(--text-tertiary)' }}>·</span>
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--accent-amber)',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              PROXY
            </span>
          </div>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            This Week in Parliament
          </h1>
          <p
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              color: 'var(--text-tertiary)',
              marginTop: 4,
              marginBottom: 0,
            }}
          >
            {subtitle}
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: 'var(--text-secondary)',
              padding: '4px 10px',
              border: '1px solid var(--border-subtle)',
              background: 'transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
            Change week
          </button>
          <button
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: 'var(--text-secondary)',
              padding: '4px 10px',
              border: '1px solid var(--border-subtle)',
              background: 'transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            PDF
          </button>
        </div>
      </div>

      <WeekAtGlance
        contributions={weekContributions}
        activeMpCount={activeMpCount}
        totalMpCount={status.mp_count}
        prevWeekCount={prevWeekCount}
      />

      <TopStory contribution={weekContributions[0] ?? null} />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <WeeklyTimeline contributions={weekContributions} />
        <WhoWasActive contributions={weekContributions} mps={mps} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <ByTheNumbers contributions={weekContributions} />
        <HotTopics contributions={weekContributions} />
      </div>

      <RecentContributions contributions={weekContributions} />
      <CaveatBanner />
    </div>
  );
}

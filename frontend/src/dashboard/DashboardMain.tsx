import { useState } from 'react';
import { DashboardData } from './useDashboardData';
import WeekAtGlance from './WeekAtGlance';
import TopStory from './TopStory';
import WeeklyTimeline from './WeeklyTimeline';
import WhoWasActive from './WhoWasActive';
import ByTheNumbers from './ByTheNumbers';
import HotTopics from './HotTopics';
import RecentContributions from './RecentContributions';
import CaveatBanner from './CaveatBanner';
import AnalyticsOverview from '../analytics/AnalyticsOverview';

interface DashboardMainProps {
  data: DashboardData;
}

const MON_ABRV = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function formatDateRange(weekStart: string | null, weekEnd: string | null): string {
  if (!weekStart || !weekEnd) return 'No sitting days';
  const s = new Date(weekStart);
  const e = new Date(weekEnd);
  return `${s.getDate()}–${e.getDate()} ${MON_ABRV[s.getMonth()]} ${s.getFullYear()}`;
}

export default function DashboardMain({ data }: DashboardMainProps) {
  const { weekContributions, weekStart, weekEnd, sittingDays, prevWeekCount, mps, status, narrative } = data;
  const [weekSelectorOpen, setWeekSelectorOpen] = useState(false);
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
          {narrative?.narrative_highlights?.headline_story && (
            <p
              style={{
                fontSize: 12,
                color: 'var(--text-secondary)',
                marginTop: 4,
                marginBottom: 0,
                lineHeight: 1.5,
                maxWidth: 520,
              }}
            >
              {narrative.narrative_highlights.headline_story}
            </p>
          )}
          {narrative?.narrative_highlights?.deferral_alert && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                marginTop: 6,
                padding: '4px 8px',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--accent-red)',
                borderLeft: '3px solid var(--accent-red)',
              }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--accent-red)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-red)' }}>
                {narrative.narrative_highlights.deferral_alert}
              </span>
            </div>
          )}
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
          {weekContributions.length > 0 && (
            <p
              style={{
                fontSize: 13,
                color: 'var(--text-secondary)',
                marginTop: 12,
                marginBottom: 4,
                lineHeight: 1.6,
                maxWidth: 600,
              }}
            >
              This week, Parliament sat for {sittingDays} day{sittingDays === 1 ? '' : 's'} and recorded{' '}
              {weekContributions.length} contribution{weekContributions.length === 1 ? '' : 's'} from{' '}
              {activeMpCount} active MP{activeMpCount === 1 ? '' : 's'} across{' '}
              {new Set(weekContributions.map(c => c.ministry_addressed).filter(Boolean)).size} ministries.
              {narrative?.summary_metrics?.top_addressed_ministry && (
                <>
                  {' '}The most addressed ministry was{' '}
                  <strong>{narrative.summary_metrics.top_addressed_ministry}</strong>
                  {narrative.summary_metrics.top_ministry_count > 0 && (
                    <> with {narrative.summary_metrics.top_ministry_count} question{narrative.summary_metrics.top_ministry_count === 1 ? '' : 's'}</>
                  )}.
                </>
              )}
              {prevWeekCount > 0 && weekContributions.length > prevWeekCount && (
                <> Activity increased {Math.round(((weekContributions.length - prevWeekCount) / prevWeekCount) * 100)}% from the previous week ({prevWeekCount} contributions).</>
              )}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={() => setWeekSelectorOpen(!weekSelectorOpen)}
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
            {weekSelectorOpen ? 'Close selector' : 'Change week'}
          </button>
          <button
            onClick={() => window.print()}
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

      <AnalyticsOverview />

      <WeekAtGlance
        contributions={weekContributions}
        activeMpCount={activeMpCount}
        totalMpCount={status.mp_count}
        prevWeekCount={prevWeekCount}
        narrative={narrative}
      />

      <TopStory
        contribution={weekContributions[0] ?? null}
        narrative={narrative?.top_story ?? null}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <WeeklyTimeline contributions={weekContributions} narrative={narrative} />
        <WhoWasActive
          contributions={weekContributions}
          mps={mps}
          mpFocus={narrative?.mp_focus ?? null}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <ByTheNumbers contributions={weekContributions} narrative={narrative} />
        <HotTopics
          contributions={weekContributions}
          narrativeTopics={narrative?.hot_topics ?? null}
        />
      </div>

      {weekSelectorOpen && (
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 12, marginTop: 4, marginBottom: 16 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Week Navigator
          </span>
          <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: '8px 0 0 0' }}>
            Currently showing: {weekLabel}. This dashboard shows the most recent parliamentary week.
            The API provides data for the latest available week. To view a different week, select it on the
            {' '}<a href="/feed" style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}>Feed page</a> using the date filters.
          </p>
        </div>
      )}

      <RecentContributions contributions={weekContributions} />
      <CaveatBanner />
    </div>
  );
}

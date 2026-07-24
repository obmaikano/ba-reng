import { useAnalytics } from '../hooks/useAnalytics';

interface ScorecardProps {
  mpId?: number;
}

const GRADE_COLOR: Record<string, string> = {
  A: 'var(--accent-green)',
  C: 'var(--accent-amber)',
  F: 'var(--accent-red)',
};

const GRADE_BG: Record<string, string> = {
  A: 'rgba(22,163,74,0.15)',
  C: 'rgba(245,166,35,0.15)',
  F: 'rgba(239,68,68,0.15)',
};

function computeGrade(deferralRate: number, lagDays: number): 'A' | 'C' | 'F' {
  if (deferralRate < 10 && lagDays < 14) return 'A';
  if (deferralRate > 30 || lagDays > 30) return 'F';
  return 'C';
}

export default function ScorecardGrid({ mpId }: ScorecardProps) {
  const { dodgeData, claiData, loading, error } = useAnalytics(mpId);

  if (loading || error) return null;

  const worstDodge = dodgeData.length > 0 ? dodgeData[0] : null;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
      {/* Ministerial Responsiveness */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 16 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Executive Responsiveness
        </span>
        {worstDodge ? (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: 4 }}>
              <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                {worstDodge.ministry}
              </h3>
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700,
                color: GRADE_COLOR[computeGrade(worstDodge.deferral_rate_pct, worstDodge.avg_response_lag_days)],
                background: GRADE_BG[computeGrade(worstDodge.deferral_rate_pct, worstDodge.avg_response_lag_days)],
                border: `2px solid ${GRADE_COLOR[computeGrade(worstDodge.deferral_rate_pct, worstDodge.avg_response_lag_days)]}`,
                width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {computeGrade(worstDodge.deferral_rate_pct, worstDodge.avg_response_lag_days)}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 10 }}>
              <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 8 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Deferral Rate</span>
                <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700, color: 'var(--accent-amber)', marginTop: 2 }}>
                  {worstDodge.deferral_rate_pct}%
                </span>
              </div>
              <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 8 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Avg Answer Lag</span>
                <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700, color: 'var(--accent-blue)', marginTop: 2 }}>
                  {worstDodge.avg_response_lag_days}d
                </span>
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', marginTop: 10, borderTop: '1px solid var(--border-subtle)', paddingTop: 8 }}>
              High deferral rates indicate questions deferred to a Later Date.
            </div>
          </>
        ) : (
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', marginTop: 8 }}>No deferral data available yet.</p>
        )}
      </div>

      {/* CLAI Scorecard */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 16 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Constituency Local Grounding (CLAI)
        </span>
        {claiData && !('error' in claiData) ? (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginTop: 4 }}>
              <h3 style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                {claiData.constituency}
              </h3>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: 'var(--accent-blue)' }}>
                {claiData.clai_score_pct}%
                <span style={{ fontSize: 9, fontWeight: 400, color: 'var(--text-tertiary)', marginLeft: 4 }}>CLAI</span>
              </span>
            </div>
            <div style={{ marginTop: 10, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>Local Mentions</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 600, color: 'var(--accent-green)' }}>
                  {claiData.local_mentions} of {claiData.total_contributions}
                </span>
              </div>
              <div style={{ height: 4, background: 'var(--border-subtle)', borderRadius: 0 }}>
                <div style={{
                  height: 4, width: `${Math.min(claiData.clai_score_pct, 100)}%`,
                  background: claiData.clai_score_pct >= 50 ? 'var(--accent-green)' : claiData.clai_score_pct >= 25 ? 'var(--accent-amber)' : 'var(--accent-red)',
                }} />
              </div>
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', marginTop: 10, borderTop: '1px solid var(--border-subtle)', paddingTop: 8 }}>
              Cross-referenced against official gazetteer settlement registries.
            </div>
          </>
        ) : (
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', marginTop: 8 }}>
            Select an MP to view local alignment data.
          </p>
        )}
      </div>
    </div>
  );
}

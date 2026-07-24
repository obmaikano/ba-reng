import { useAnalytics } from '../hooks/useAnalytics';

export default function AnalyticsOverview() {
  const { dodgeData, velocityData, loading, error } = useAnalytics();

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
          Loading analytics…
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 16, background: 'var(--bg-elevated)', border: '1px solid var(--accent-red)', marginBottom: 16 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-red)' }}>{error}</span>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '7fr 5fr', gap: 16, marginBottom: 16 }}>
      {/* Ministerial Deferral Scorecard */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
            MINISTERIAL DEFERRAL SCORECARD
          </h3>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--accent-amber)', border: '1px solid var(--accent-amber)', padding: '2px 6px' }}>
            30-DAY LOOKBACK
          </span>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: 10 }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-tertiary)' }}>
              <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 500 }}>MINISTRY</th>
              <th style={{ textAlign: 'center', padding: '6px 8px', fontWeight: 500 }}>Q</th>
              <th style={{ textAlign: 'center', padding: '6px 8px', fontWeight: 500 }}>DEF</th>
              <th style={{ textAlign: 'center', padding: '6px 8px', fontWeight: 500 }}>RATE</th>
              <th style={{ textAlign: 'center', padding: '6px 8px', fontWeight: 500 }}>LAG (d)</th>
            </tr>
          </thead>
          <tbody>
            {dodgeData.length === 0 ? (
              <tr><td colSpan={5} style={{ padding: 16, textAlign: 'center', color: 'var(--text-tertiary)' }}>No data available.</td></tr>
            ) : dodgeData.slice(0, 8).map((item, i) => (
              <tr key={i} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
                <td style={{ padding: '6px 8px', color: 'var(--text-primary)', maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.ministry}</td>
                <td style={{ padding: '6px 8px', textAlign: 'center', color: 'var(--accent-blue)' }}>{item.total_questions}</td>
                <td style={{ padding: '6px 8px', textAlign: 'center', color: 'var(--accent-amber)' }}>{item.deferred_count}</td>
                <td style={{ padding: '6px 8px', textAlign: 'center', fontWeight: 600, color: item.deferral_rate_pct > 30 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                  {item.deferral_rate_pct}%
                </td>
                <td style={{ padding: '6px 8px', textAlign: 'center', color: 'var(--text-secondary)' }}>{item.avg_response_lag_days}d</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Topic Velocity Radar */}
      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>
            TOPIC VELOCITY RADAR (&Delta;f)
          </h3>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--accent-blue)', border: '1px solid var(--accent-blue)', padding: '2px 6px' }}>
            WEEK-OVER-WEEK
          </span>
        </div>
        {velocityData.length === 0 ? (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>No trending topics detected.</span>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {velocityData.slice(0, 8).map((item, i) => (
              <div key={i} style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: '8px 10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', textTransform: 'capitalize' }}>{item.keyword}</span>
                  <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                    {item.current_frequency} now vs {item.prior_avg_frequency} avg
                  </span>
                </div>
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700,
                  color: item.velocity_delta_pct > 100 ? 'var(--accent-red)' : item.velocity_delta_pct > 0 ? 'var(--accent-green)' : 'var(--text-tertiary)',
                }}>
                  {item.velocity_delta_pct > 0 ? `+${item.velocity_delta_pct}%` : `${item.velocity_delta_pct}%`}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

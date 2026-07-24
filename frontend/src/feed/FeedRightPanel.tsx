import { useNavigate } from 'react-router-dom';
import { MpSummary } from '../dashboard/types';

interface FeedRightPanelProps {
  mps: MpSummary[];
  unresolvedCount: number;
}

const sectionHeader: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: 'var(--text-primary)',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  margin: 0,
};

export default function FeedRightPanel({ mps, unresolvedCount }: FeedRightPanelProps) {
  const navigate = useNavigate();
  const top5 = [...mps]
    .sort((a, b) => b.participation_index.participation_index - a.participation_index.participation_index)
    .slice(0, 5);
  const maxScore = Math.max(1, ...top5.map((mp) => mp.participation_index.participation_index));

  return (
    <div>
      <div style={{ padding: 16, borderBottom: '1px solid var(--border-default)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <h3 style={sectionHeader}>Participation Index</h3>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-amber)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            PROXY
          </span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {top5.map((mp, i) => {
            const score = mp.participation_index.participation_index;
            return (
              <div
                key={mp.id}
                onClick={() => navigate(`/mp/${mp.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', width: 16, textAlign: 'right' }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 2 }}>
                      <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {mp.name}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent-blue)', fontWeight: 600 }}>{score}</span>
                    </div>
                    <div style={{ height: 2, background: 'var(--bg-elevated)' }}>
                      <div style={{ height: 2, background: 'var(--accent-blue)', width: `${(score / maxScore) * 100}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        <span
          onClick={() => navigate('/rankings')}
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--accent-blue)',
            cursor: 'pointer',
            display: 'inline-block',
            marginTop: 12,
          }}
        >
          View full leaderboard &rarr;
        </span>
      </div>

      <div style={{ padding: 16, borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 2, flexShrink: 0 }}>
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <div>
            <h4 style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-amber)', margin: 0, marginBottom: 4 }}>
              Constraint: No Attendance Data
            </h4>
            <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
              Botswana Parliament does not publish attendance records. This index tracks{' '}
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>RECORDED_CONTRIBUTIONS</span> only.
            </p>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-blue)', cursor: 'pointer', display: 'inline-block', marginTop: 4 }}>
              VIEW_METHODOLOGY &rarr;
            </span>
          </div>
        </div>
      </div>

      <div style={{ padding: 16 }}>
        <h3 style={sectionHeader}>Unresolved Entities</h3>
        <p style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.4, margin: 0, marginBottom: 12 }}>
          These names could not be matched to the MP roster.
        </p>
        {unresolvedCount > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 10px', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)' }}>
              <div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>Unresolved entries</div>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--accent-amber)', textTransform: 'uppercase', letterSpacing: '0.05em', border: '1px solid rgba(245,166,35,0.3)', background: 'rgba(245,166,35,0.1)', padding: '2px 6px' }}>
                {unresolvedCount} PENDING
              </span>
            </div>
          </div>
        ) : (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
            All entities resolved.
          </span>
        )}
      </div>
    </div>
  );
}

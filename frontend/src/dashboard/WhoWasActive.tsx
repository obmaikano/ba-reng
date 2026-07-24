import { useNavigate } from 'react-router-dom';
import { Contribution, MpSummary } from './types';
import { narrativeSection, sectionTitle, mono, surfaceElevated, avatarMono, initials } from './styles';

interface WhoWasActiveProps {
  contributions: Contribution[];
  mps: MpSummary[];
}

interface WeeklyMpActivity {
  mp: MpSummary;
  count: number;
}

function rankByWeeklyActivity(contributions: Contribution[], mps: MpSummary[]): WeeklyMpActivity[] {
  const mpsById = new Map(mps.map((mp) => [mp.id, mp]));
  const counts = new Map<number, number>();
  for (const c of contributions) {
    if (c.mp_id === null) continue;
    counts.set(c.mp_id, (counts.get(c.mp_id) ?? 0) + 1);
  }

  return Array.from(counts.entries())
    .map(([mpId, count]) => {
      const mp = mpsById.get(mpId);
      return mp ? { mp, count } : null;
    })
    .filter((entry): entry is WeeklyMpActivity => entry !== null)
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);
}

export default function WhoWasActive({ contributions, mps }: WhoWasActiveProps) {
  const navigate = useNavigate();
  const top5 = rankByWeeklyActivity(contributions, mps);

  return (
    <div style={narrativeSection}>
      <div style={{ ...sectionTitle, display: 'flex', alignItems: 'center', gap: 4 }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        WHO WAS ACTIVE THIS WEEK
      </div>
      {top5.length === 0 ? (
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>No activity recorded this week.</span>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {top5.map(({ mp, count }, index) => (
            <div
              key={mp.id}
              onClick={() => navigate(`/mp/${mp.id}`)}
              style={{
                ...surfaceElevated,
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 10px',
                cursor: 'pointer',
              }}
            >
              <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', width: 14, textAlign: 'right' }}>
                {index + 1}
              </span>
              <div style={avatarMono(28)}>{initials(mp.name)}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 500,
                    color: 'var(--text-primary)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {mp.name}
                </div>
                <div style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                  {mp.party} · {mp.constituency}
                </div>
              </div>
              <span style={{ ...mono, fontSize: 13, fontWeight: 600, color: 'var(--accent-blue)' }}>
                {count}
              </span>
              <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>contrib</span>
            </div>
          ))}
        </div>
      )}
      <div style={{ marginTop: 8, textAlign: 'center' }}>
        <span
          onClick={() => navigate('/rankings')}
          style={{ ...mono, fontSize: 10, color: 'var(--accent-blue)', cursor: 'pointer' }}
        >
          View full leaderboard →
        </span>
        <span style={{ color: 'var(--text-tertiary)', margin: '0 8px' }}>·</span>
        <span
          onClick={() => navigate('/compare')}
          style={{ ...mono, fontSize: 10, color: 'var(--accent-blue)', cursor: 'pointer' }}
        >
          Compare MPs →
        </span>
      </div>
    </div>
  );
}

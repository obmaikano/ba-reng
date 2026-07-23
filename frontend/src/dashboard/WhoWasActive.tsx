import { useNavigate } from 'react-router-dom';
import { MpSummary } from './types';
import { card, sectionTitle, mono, surfaceElevated, avatarMono, initials } from './styles';

interface WhoWasActiveProps {
  mps: MpSummary[];
}

export default function WhoWasActive({ mps }: WhoWasActiveProps) {
  const navigate = useNavigate();
  const top5 = [...mps]
    .sort((a, b) => b.contribution_count - a.contribution_count)
    .slice(0, 5);

  return (
    <div style={card}>
      <div style={sectionTitle}>Who Was Active</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {top5.map((mp, index) => (
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
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {mp.name}
              </div>
              <div style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                {mp.party} · {mp.constituency}
              </div>
            </div>
            <span style={{ ...mono, fontSize: 13, fontWeight: 600, color: 'var(--accent-blue)' }}>
              {mp.contribution_count}
            </span>
            <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>contrib</span>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 10, textAlign: 'center' }}>
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

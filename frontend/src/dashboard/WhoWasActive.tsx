import { useNavigate } from 'react-router-dom';
import { MpSummary } from './types';
import { card, sectionTitle, mono } from './styles';

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
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {top5.map((mp, index) => (
          <div
            key={mp.id}
            onClick={() => navigate(`/mp/${mp.id}`)}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer',
              padding: '4px 0',
            }}
          >
            <span style={{ fontSize: 13, color: 'var(--text-primary)' }}>
              <span style={{ ...mono, color: 'var(--text-tertiary)', marginRight: 8 }}>{index + 1}</span>
              {mp.name}
              <span style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 6 }}>
                ({mp.constituency})
              </span>
            </span>
            <span style={{ ...mono, fontSize: 12, color: 'var(--accent-blue)' }}>
              {mp.contribution_count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

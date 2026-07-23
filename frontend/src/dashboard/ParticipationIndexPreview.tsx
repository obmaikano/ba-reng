import { useNavigate } from 'react-router-dom';
import { MpSummary } from './types';
import { sectionTitle, mono, barThin } from './styles';

interface ParticipationIndexPreviewProps {
  mps: MpSummary[];
}

export default function ParticipationIndexPreview({ mps }: ParticipationIndexPreviewProps) {
  const navigate = useNavigate();
  const top5 = [...mps]
    .sort((a, b) => b.participation_index.participation_index - a.participation_index.participation_index)
    .slice(0, 5);
  const maxScore = Math.max(1, ...top5.map((mp) => mp.participation_index.participation_index));

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={sectionTitle}>Participation Index</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {top5.map((mp, index) => {
          const score = mp.participation_index.participation_index;
          return (
            <div
              key={mp.id}
              onClick={() => navigate(`/mp/${mp.id}`)}
              style={{ cursor: 'pointer' }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', width: 16, textAlign: 'right' }}>
                  {String(index + 1).padStart(2, '0')}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 2 }}>
                    <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {mp.name}
                    </span>
                    <span style={{ ...mono, fontSize: 12, color: 'var(--accent-blue)', fontWeight: 600 }}>{score}</span>
                  </div>
                  <div style={barThin}>
                    <div
                      style={{
                        height: 2,
                        background: 'var(--accent-blue)',
                        width: `${(score / maxScore) * 100}%`,
                      }}
                    />
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
          ...mono,
          fontSize: 10,
          color: 'var(--accent-blue)',
          cursor: 'pointer',
          display: 'inline-block',
          marginTop: 12,
        }}
      >
        View full leaderboard →
      </span>
    </div>
  );
}

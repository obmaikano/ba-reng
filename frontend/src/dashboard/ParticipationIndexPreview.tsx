import { useNavigate } from 'react-router-dom';
import { MpSummary } from './types';
import { sectionTitle, mono } from './styles';

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
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                <span style={{ fontSize: 12, color: 'var(--text-primary)' }}>
                  <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', marginRight: 6 }}>
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  {mp.name}
                </span>
                <span style={{ ...mono, fontSize: 12, color: 'var(--accent-blue)' }}>{score}</span>
              </div>
              <div style={{ height: 2, background: 'var(--bg-elevated)' }}>
                <div
                  style={{ height: 2, width: `${(score / maxScore) * 100}%`, background: 'var(--accent-blue)' }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <span
        onClick={() => navigate('/rankings')}
        style={{ ...mono, fontSize: 11, color: 'var(--accent-blue)', cursor: 'pointer', display: 'inline-block', marginTop: 10 }}
      >
        View full leaderboard →
      </span>
    </div>
  );
}

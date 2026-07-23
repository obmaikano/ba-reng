import { useNavigate } from 'react-router-dom';
import { StatusData } from './useDashboardData';
import { sectionTitle, mono } from './styles';

interface SystemHealthPanelProps {
  status: StatusData;
}

const rowStyle = { display: 'flex', justifyContent: 'space-between', fontSize: 11 } as const;
const labelStyle = { color: 'var(--text-secondary)' } as const;

export default function SystemHealthPanel({ status }: SystemHealthPanelProps) {
  const navigate = useNavigate();
  const crawlHealthy = status.last_crawl?.status === 'SUCCESS';
  const hasUnresolved = status.unresolved_entity_count > 0;

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={sectionTitle}>System Health</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={rowStyle}>
          <span style={labelStyle}>Crawl status</span>
          <span style={{ ...mono, color: crawlHealthy ? 'var(--accent-green)' : 'var(--accent-amber)', display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ color: crawlHealthy ? 'var(--accent-green)' : 'var(--accent-amber)' }}>●</span>
            {crawlHealthy ? 'Healthy' : status.last_crawl?.status ?? 'Unknown'}
          </span>
        </div>
        <div style={rowStyle}>
          <span style={labelStyle}>Last crawl</span>
          <span style={{ ...mono, color: 'var(--text-tertiary)' }}>
            {status.last_crawl?.started_at.slice(0, 16) ?? '—'}
          </span>
        </div>
        <div style={rowStyle}>
          <span style={labelStyle}>Documents parsed</span>
          <span style={{ ...mono, color: 'var(--accent-blue)' }}>{status.document_count}</span>
        </div>
        <div style={rowStyle}>
          <span style={labelStyle}>Unresolved entities</span>
          <span style={{ ...mono, color: hasUnresolved ? 'var(--accent-amber)' : 'var(--accent-green)' }}>
            {status.unresolved_entity_count}
            {hasUnresolved && (
              <>
                {' · '}
                <span
                  onClick={() => navigate('/admin/entities')}
                  style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}
                >
                  Review
                </span>
              </>
            )}
          </span>
        </div>
        <div style={rowStyle}>
          <span style={labelStyle}>Session</span>
          <span style={{ ...mono, color: 'var(--text-tertiary)' }}>13th Parliament</span>
        </div>
      </div>
    </div>
  );
}

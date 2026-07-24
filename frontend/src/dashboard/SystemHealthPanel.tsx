import { useNavigate } from 'react-router-dom';
import { StatusData } from './useDashboardData';
import { sectionTitle, mono, statusDot } from './styles';

interface SystemHealthPanelProps {
  status: StatusData;
}

export default function SystemHealthPanel({ status }: SystemHealthPanelProps) {
  const navigate = useNavigate();
  const crawlHealthy = status.last_crawl?.status === 'SUCCESS';
  const hasUnresolved = status.unresolved_entity_count > 0;

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={sectionTitle}>System Health</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
          <span style={{ color: 'var(--text-secondary)' }}>Update status</span>
          <span
            style={{
              ...mono,
              color: crawlHealthy ? 'var(--accent-green)' : 'var(--accent-amber)',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
            }}
          >
            <span
              style={{
                ...statusDot,
                background: crawlHealthy ? 'var(--accent-green)' : 'var(--accent-amber)',
              }}
            />
            {crawlHealthy ? 'Healthy' : status.last_crawl?.status ?? 'Unknown'}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
          <span style={{ color: 'var(--text-secondary)' }}>Last update</span>
          <span style={{ ...mono, color: 'var(--text-tertiary)' }}>
            {status.last_crawl
              ? status.last_crawl.started_at.slice(5, 10).replace('-', ' ') + ' ' + status.last_crawl.started_at.slice(11, 16)
              : '—'}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
          <span style={{ color: 'var(--text-secondary)' }}>Documents read</span>
          <span style={{ ...mono, color: 'var(--accent-blue)' }}>{status.document_count}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
          <span style={{ color: 'var(--text-secondary)' }}>Names not matched</span>
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
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
          <span style={{ color: 'var(--text-secondary)' }}>Parliament</span>
          <span style={{ ...mono, color: 'var(--text-tertiary)' }}>13th, Session 5</span>
        </div>
      </div>
    </div>
  );
}

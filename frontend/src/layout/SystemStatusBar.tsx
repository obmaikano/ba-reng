import { useEffect, useState } from 'react';
import { get } from '../api';

interface StatusData {
  mp_count: number;
  contribution_count: number;
  document_count: number;
  unresolved_entity_count: number;
  last_crawl: { started_at: string; status: string; new_documents: number } | null;
}

export default function SystemStatusBar() {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    get<StatusData>('/api/v1/status')
      .then(setStatus)
      .catch(() => setError(true));
  }, []);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 16,
        height: 28,
        padding: '0 12px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-elevated)',
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        color: 'var(--text-tertiary)',
      }}
    >
      {error ? (
        <span style={{ color: 'var(--accent-red)' }}>API offline</span>
      ) : !status ? (
        <span>Loading...</span>
      ) : (
        <>
          <span style={{ color: 'var(--accent-green)' }}>●</span>
          <span>{status.mp_count} MPs</span>
          <span>{status.contribution_count} contributions</span>
          <span>{status.document_count} docs</span>
          <span>
            {status.unresolved_entity_count > 0 ? (
              <span style={{ color: 'var(--accent-amber)' }}>
                {status.unresolved_entity_count} unresolved
              </span>
            ) : (
              <span style={{ color: 'var(--accent-green)' }}>0 unresolved</span>
            )}
          </span>
          {status.last_crawl && (
            <span>
              Last crawl: {status.last_crawl.started_at.slice(0, 10)} ({status.last_crawl.new_documents} new)
            </span>
          )}
        </>
      )}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { get } from '../api';

interface StatusData {
  mp_count: number;
  contribution_count: number;
  document_count: number;
  unresolved_entity_count: number;
  last_crawl: { started_at: string; status: string; new_documents: number } | null;
}

const CRAWL_SOURCE = 'botswanaspeaks.gov.bw';

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
        justifyContent: 'space-between',
        height: 26,
        padding: '0 20px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        color: 'var(--text-tertiary)',
      }}
    >
      {error ? (
        <span style={{ color: 'var(--accent-red)' }}>SERVICE_OFFLINE</span>
      ) : !status ? (
        <span>LOADING...</span>
      ) : (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: 'var(--accent-green)' }}>●</span> COLLECTING_DATA
            </span>
            <span>SOURCE: {CRAWL_SOURCE}</span>
            {status.last_crawl && <span>LAST_UPDATE: {status.last_crawl.started_at}</span>}
            <span>DOCUMENTS_READ: {status.document_count}</span>
          </div>
          <span style={{ color: 'var(--accent-amber)', display: 'flex', alignItems: 'center', gap: 4 }}>
            ⚠ PROXY_METRIC
          </span>
        </>
      )}
    </div>
  );
}

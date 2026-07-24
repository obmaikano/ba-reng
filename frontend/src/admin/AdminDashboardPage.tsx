import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Spinner, Intent, Tag } from '@blueprintjs/core';
import { get, post } from '../api';
import { useAuth } from '../auth/AuthContext';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DashboardData {
  mp_count: number;
  contribution_count: number;
  document_count: number;
  unresolved_entity_count: number;
  resolved_entity_count: number;
  last_crawl: {
    started_at: string;
    finished_at: string | null;
    status: string;
    new_documents: number;
    errors: number;
  } | null;
  crawl_running: boolean;
}

interface CrawlRun {
  id: number;
  started_at: string;
  finished_at: string | null;
  source: string;
  status: string;
  new_documents: number;
  errors: number;
  run_type: string;
}

// ---------------------------------------------------------------------------
// Shared styles
// ---------------------------------------------------------------------------

const CARD: React.CSSProperties = {
  border: '1px solid #1F242E',
  background: '#12161C',
  padding: '16px 20px',
};

const CARD_TITLE: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
  color: '#738091',
  marginBottom: 6,
};

const STAT_VALUE: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 22,
  fontWeight: 600,
  color: '#E8EDF2',
};

const SECTION_TITLE: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 11,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  color: '#738091',
  marginBottom: 12,
};

const statusColor = (s: string): string => {
  switch (s) {
    case 'SUCCESS': return '#15B371';
    case 'RUNNING': return '#2B95D6';
    case 'PARTIAL': return '#D9822B';
    case 'ERROR': return '#F55656';
    default: return '#738091';
  }
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function AdminDashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [crawlRuns, setCrawlRuns] = useState<CrawlRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [d, runs] = await Promise.all([
        get<DashboardData>('/api/v1/admin/dashboard'),
        get<CrawlRun[]>('/api/v1/admin/crawl-runs'),
      ]);
      setData(d);
      setCrawlRuns(runs);
      setError('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleTriggerCrawl = async () => {
    setTriggering(true);
    setTriggerMsg('');
    try {
      const res = await post<{ detail: string }>('/api/v1/admin/crawl/trigger', {});
      setTriggerMsg(res.detail);
      // Poll for results after a short delay
      setTimeout(() => fetchData(), 3000);
    } catch (err: unknown) {
      setTriggerMsg(err instanceof Error ? err.message : 'Trigger failed');
    } finally {
      setTriggering(false);
    }
  };

  const isAdmin = user?.role === 'admin';

  // -----------------------------------------------------------------------
  // Loading / Error states
  // -----------------------------------------------------------------------

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300 }}>
        <Spinner size={24} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ color: '#F55656', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        {error}
        <Button minimal small intent={Intent.PRIMARY} onClick={fetchData} style={{ marginLeft: 12 }}>
          Retry
        </Button>
      </div>
    );
  }

  if (!data) return null;

  // -----------------------------------------------------------------------
  // Render
  // -----------------------------------------------------------------------

  return (
    <div style={{ maxWidth: 960 }}>
      {/* Page header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h1 style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 16,
          fontWeight: 600,
          color: '#E8EDF2',
          margin: 0,
        }}>
          Admin Dashboard
        </h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {isAdmin && (
            <Button
              intent={Intent.PRIMARY}
              small
              loading={triggering}
              disabled={data.crawl_running}
              onClick={handleTriggerCrawl}
            >
              {data.crawl_running ? 'Crawl Running…' : 'Trigger Crawl'}
            </Button>
          )}
          {triggerMsg && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#738091' }}>
              {triggerMsg}
            </span>
          )}
        </div>
      </div>

      {/* Stat cards — 4-column grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
        <div style={CARD}>
          <div style={CARD_TITLE}>Documents</div>
          <div style={STAT_VALUE}>{data.document_count.toLocaleString()}</div>
        </div>
        <div style={CARD}>
          <div style={CARD_TITLE}>Contributions</div>
          <div style={STAT_VALUE}>{data.contribution_count.toLocaleString()}</div>
        </div>
        <div style={CARD}>
          <div style={CARD_TITLE}>MPs Indexed</div>
          <div style={STAT_VALUE}>{data.mp_count}</div>
        </div>
        <div style={CARD}>
          <div style={CARD_TITLE}>Unresolved Entities</div>
          <div style={{ ...STAT_VALUE, color: data.unresolved_entity_count > 0 ? '#D9822B' : '#15B371' }}>
            {data.unresolved_entity_count}
          </div>
        </div>
      </div>

      {/* Data quality row */}
      <div style={SECTION_TITLE}>Data Quality</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
        <div style={CARD}>
          <div style={CARD_TITLE}>Entity Resolution</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: '#BDC1C9' }}>
            {data.resolved_entity_count} resolved / {data.unresolved_entity_count} unresolved
          </div>
          <div style={{
            marginTop: 8, height: 4, background: '#1F242E', borderRadius: 0,
          }}>
            <div style={{
              height: 4,
              width: `${data.resolved_entity_count + data.unresolved_entity_count > 0
                ? Math.round(data.resolved_entity_count / (data.resolved_entity_count + data.unresolved_entity_count) * 100)
                : 0}%`,
              background: '#2B95D6',
              borderRadius: 0,
            }} />
          </div>
        </div>
        <div style={CARD}>
          <div style={CARD_TITLE}>Last Crawl</div>
          {data.last_crawl ? (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#BDC1C9' }}>
              <div style={{ marginBottom: 4 }}>
                <Tag minimal style={{ background: statusColor(data.last_crawl.status), color: '#0B0E14', fontSize: 10 }}>
                  {data.last_crawl.status}
                </Tag>
              </div>
              <div style={{ color: '#738091' }}>
                {data.last_crawl.finished_at
                  ? new Date(data.last_crawl.finished_at + 'Z').toLocaleString()
                  : 'In progress…'}
              </div>
              <div style={{ marginTop: 2 }}>
                {data.last_crawl.new_documents} new docs
                {data.last_crawl.errors > 0 && ` · ${data.last_crawl.errors} errors`}
              </div>
            </div>
          ) : (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#738091' }}>
              No crawl data yet
            </div>
          )}
        </div>
        <div style={CARD}>
          <div style={CARD_TITLE}>Pipeline Status</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#BDC1C9' }}>
            <Tag minimal style={{ background: data.crawl_running ? '#2B95D6' : '#15B371', color: '#0B0E14', fontSize: 10 }}>
              {data.crawl_running ? 'CRAWLING' : 'IDLE'}
            </Tag>
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div style={SECTION_TITLE}>Quick Links</div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
        <Button minimal small onClick={() => navigate('/admin/ministry-mappings')}>
          Ministry Mappings
        </Button>
        <Button minimal small disabled title="Coming soon">
          Entity Review Queue
        </Button>
        <Button minimal small disabled title="Coming soon">
          User Management
        </Button>
      </div>

      {/* Recent crawl runs */}
      <div style={SECTION_TITLE}>Recent Crawl Runs</div>
      {crawlRuns.length === 0 ? (
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#738091' }}>
          No crawl runs recorded
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{
            width: '100%', borderCollapse: 'collapse',
            fontFamily: 'var(--font-mono)', fontSize: 11, color: '#BDC1C9',
          }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #1F242E' }}>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Started</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Source</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Type</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Status</th>
                <th style={{ textAlign: 'right', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>New Docs</th>
                <th style={{ textAlign: 'right', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Errors</th>
              </tr>
            </thead>
            <tbody>
              {crawlRuns.map((run) => (
                <tr key={run.id} style={{ borderBottom: '1px solid #1A1F27' }}>
                  <td style={{ padding: '8px 12px', color: '#738091' }}>
                    {new Date(run.started_at + 'Z').toLocaleString()}
                  </td>
                  <td style={{ padding: '8px 12px' }}>{run.source}</td>
                  <td style={{ padding: '8px 12px' }}>
                    <Tag minimal style={{ fontSize: 10, background: run.run_type === 'manual' ? '#2B95D6' : '#1F242E', color: run.run_type === 'manual' ? '#E8EDF2' : '#738091' }}>
                      {run.run_type}
                    </Tag>
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <Tag minimal style={{ background: statusColor(run.status), color: '#0B0E14', fontSize: 10 }}>
                      {run.status}
                    </Tag>
                  </td>
                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>{run.new_documents}</td>
                  <td style={{ padding: '8px 12px', textAlign: 'right', color: run.errors > 0 ? '#F55656' : '#BDC1C9' }}>
                    {run.errors}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

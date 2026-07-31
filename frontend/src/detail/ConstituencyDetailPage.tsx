import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';
import { Contribution } from '../dashboard/types';
import { typeLabel, mono } from '../dashboard/styles';

interface ConstituencyData {
  constituency: string;
  mp_name: string | null;
  party: string | null;
  contribution_count: number;
  oral_question_count: number;
  motion_count: number;
}

interface ConstituencyStats {
  info: ConstituencyData;
  contributions: Contribution[];
  total_records: number;
}

export default function ConstituencyDetailPage() {
  const { name } = useParams();
  const navigate = useNavigate();
  const [stats, setStats] = useState<ConstituencyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!name) return;
    setLoading(true);
    const constituency = decodeURIComponent(name);

    Promise.all([
      get<ConstituencyData>(`/api/v1/constituencies/${encodeURIComponent(constituency)}`),
      get<{ data: Contribution[]; total_records: number }>(
        `/api/v1/contributions?constituency=${encodeURIComponent(constituency)}&limit=50`
      ),
    ])
      .then(([info, contribResp]) => {
        setStats({
          info,
          contributions: contribResp.data || [],
          total_records: contribResp.total_records,
        });
        setError(null);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load constituency data');
        setLoading(false);
      });
  }, [name]);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>
          Loading constituency data…
        </span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ ...mono, fontSize: 12, color: 'var(--accent-red)' }}>
          {error || 'Constituency not found.'}
        </span>
      </div>
    );
  }

  const { info } = stats;
  const hasMp = info.mp_name !== null;

  return (
    <div style={{ padding: 24, maxWidth: 900 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <span style={{
          ...mono, fontSize: 10, color: 'var(--text-tertiary)',
          textTransform: 'uppercase', letterSpacing: '0.08em',
        }}>
          CONSTITUENCY PROFILE
        </span>
        <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 0 0', lineHeight: 1.3 }}>
          {info.constituency}
        </h1>
      </div>

      {/* MP Card */}
      {hasMp ? (
        <div style={{
          marginBottom: 20, padding: 16,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
          borderLeft: '3px solid var(--accent-blue)',
          display: 'flex', alignItems: 'center', gap: 14,
        }}>
          <div style={{
            width: 48, height: 48, display: 'flex', alignItems: 'center', justifyContent: 'center',
            ...mono, fontSize: 16, fontWeight: 700,
            color: 'var(--accent-blue)', border: '1px solid var(--accent-blue)',
            background: 'var(--bg-surface)', flexShrink: 0,
          }}>
            {(info.mp_name || '??').split(/\s+/).slice(0, 2).map((w: string) => w[0]).join('').toUpperCase()}
          </div>
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: 15, fontWeight: 600, color: 'var(--accent-blue)', display: 'block' }}>
              {info.mp_name}
            </span>
            <div style={{ display: 'flex', gap: 16, marginTop: 4 }}>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {info.party || 'No party'}
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                {info.contribution_count} contributions
              </span>
            </div>
          </div>
          <span
            onClick={() => navigate('/find')}
            style={{ ...mono, fontSize: 11, color: 'var(--accent-blue)', cursor: 'pointer' }}
          >
            Find MP →
          </span>
        </div>
      ) : (
        <div style={{
          marginBottom: 20, padding: 14,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
          borderLeft: '3px solid var(--accent-amber)',
        }}>
          <span style={{ ...mono, fontSize: 11, color: 'var(--accent-amber)' }}>
            No MP found for this constituency in the database.
          </span>
        </div>
      )}

      {/* Stats row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 12 }}>
          <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block' }}>
            Total
          </span>
          <span style={{ ...mono, fontSize: 22, fontWeight: 700, color: 'var(--accent-blue)', display: 'block', marginTop: 4 }}>
            {info.contribution_count}
          </span>
        </div>
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 12 }}>
          <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block' }}>
            Questions
          </span>
          <span style={{ ...mono, fontSize: 22, fontWeight: 700, color: 'var(--accent-blue)', display: 'block', marginTop: 4 }}>
            {info.oral_question_count}
          </span>
        </div>
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 12 }}>
          <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block' }}>
            Motions
          </span>
          <span style={{ ...mono, fontSize: 22, fontWeight: 700, color: 'var(--accent-amber)', display: 'block', marginTop: 4 }}>
            {info.motion_count}
          </span>
        </div>
      </div>

      {/* Contributions */}
      <div>
        <span style={{
          ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase',
          letterSpacing: '0.08em', display: 'block', marginBottom: 12,
        }}>
          Recent Contributions
        </span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {stats.contributions.map((c) => (
            <div
              key={c.id}
              onClick={() => navigate(`/contribution/${c.id}`)}
              style={{
                background: 'var(--bg-elevated)', border: '1px solid var(--border-default)',
                padding: '10px 12px', cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                <span style={{
                  ...mono, fontSize: 8, textTransform: 'uppercase',
                  padding: '1px 5px', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)',
                }}>
                  {typeLabel(c.contribution_type)}
                </span>
                <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                  {new Date(c.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                </span>
                {c.mp_name && (
                  <span style={{ ...mono, fontSize: 9, color: 'var(--accent-blue)', marginLeft: 'auto' }}>
                    {c.mp_name}
                  </span>
                )}
              </div>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4, display: 'block' }}>
                {c.subject_text.slice(0, 150)}{c.subject_text.length > 150 ? '…' : ''}
              </span>
            </div>
          ))}
          {stats.contributions.length === 0 && (
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)', padding: 12 }}>
              No contributions found for this constituency.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

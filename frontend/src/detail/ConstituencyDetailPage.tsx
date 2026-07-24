import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';
import { Contribution } from '../dashboard/types';
import { typeLabel } from '../dashboard/styles';

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
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading constituency data…
        </span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {error || 'Constituency not found.'}
        </span>
        <div style={{ marginTop: 12 }}>
          <span onClick={() => navigate('/find')} style={{ color: 'var(--accent-blue)', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            ← Find MP
          </span>
        </div>
      </div>
    );
  }

  const { info } = stats;
  const hasMp = info.mp_name !== null;

  return (
    <div style={{ padding: 24 }}>
      {/* Breadcrumb */}
      <div style={{ marginBottom: 16, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>
        <span onClick={() => navigate('/find')} style={{ cursor: 'pointer', color: 'var(--accent-blue)' }}>Find MP</span>
        <span style={{ margin: '0 6px' }}>→</span>
        <span>{info.constituency}</span>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)',
          textTransform: 'uppercase', letterSpacing: '0.08em',
        }}>
          CONSTITUENCY PROFILE
        </span>
        <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
          {info.constituency}
        </h1>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
          {info.contribution_count} contribution{info.contribution_count === 1 ? '' : 's'} on record
        </p>
      </div>

      {/* MP Card */}
      {hasMp && (
        <div
          onClick={() => navigate(`/find`)}
          style={{
            marginBottom: 20, padding: 16,
            background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
            borderLeft: '3px solid var(--accent-blue)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 14,
          }}
        >
          <div style={{
            width: 44, height: 44, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 700,
            color: 'var(--accent-blue)', border: '1px solid var(--accent-blue)',
            background: 'var(--bg-surface)', flexShrink: 0,
          }}>
            {(info.mp_name || '??').split(/\s+/).slice(0, 2).map((w: string) => w[0]).join('').toUpperCase()}
          </div>
          <div>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent-blue)' }}>
              {info.mp_name}
            </span>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
              {info.party || 'No party'} · {info.contribution_count} contributions
            </div>
          </div>
          <span style={{ marginLeft: 'auto', color: 'var(--accent-blue)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            Find MP →
          </span>
        </div>
      )}

      {!hasMp && (
        <div style={{
          marginBottom: 20, padding: 14,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
          borderLeft: '3px solid var(--accent-amber)',
        }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-amber)' }}>
            No MP found for this constituency in the current database.
          </span>
        </div>
      )}

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
        <StatCard label="Total Contributions" value={String(info.contribution_count)} color="var(--accent-blue)" />
        <StatCard label="Oral Questions" value={String(info.oral_question_count)} color="var(--accent-blue)" />
        <StatCard label="Motions" value={String(info.motion_count)} color="var(--accent-amber)" />
      </div>

      {/* Contributions */}
      <div>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 10 }}>
          Contributions from this Constituency
        </span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {stats.contributions.map((c) => (
            <div
              key={c.id}
              onClick={() => navigate(`/contribution/${c.id}`)}
              style={{
                background: 'var(--bg-elevated)', border: '1px solid var(--border-default)',
                padding: 10, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
              }}
            >
              <span style={{
                fontFamily: 'var(--font-mono)', fontSize: 9, textTransform: 'uppercase',
                padding: '2px 6px', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)',
                flexShrink: 0,
              }}>
                {typeLabel(c.contribution_type)}
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {c.subject_text.slice(0, 120)}{c.subject_text.length > 120 ? '…' : ''}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                {new Date(c.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
              </span>
            </div>
          ))}
          {stats.contributions.length === 0 && (
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)', padding: 12 }}>No contributions found for this constituency.</span>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 12 }}>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </span>
      <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color, marginTop: 4 }}>
        {value}
      </span>
    </div>
  );
}

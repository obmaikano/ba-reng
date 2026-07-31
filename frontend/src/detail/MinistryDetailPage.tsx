import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';
import { Contribution } from '../dashboard/types';
import { typeLabel, mono } from '../dashboard/styles';

interface MinistryStats {
  ministry: string;
  total_contributions: number;
  unique_mps: number;
  top_mps: Array<{ mp_name: string; mp_id: number; party: string; count: number }>;
  contributions: Contribution[];
}

export default function MinistryDetailPage() {
  const { name } = useParams();
  const navigate = useNavigate();
  const [stats, setStats] = useState<MinistryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!name) return;
    setLoading(true);
    const ministry = decodeURIComponent(name);

    get<{ data: Contribution[]; total_records: number }>(
      `/api/v1/contributions?ministry=${encodeURIComponent(ministry)}&limit=100`
    )
      .then((resp) => {
        const contribs = resp.data || [];
        const mpMap = new Map<number, { mp_name: string; party: string; count: number }>();
        for (const c of contribs) {
          if (c.mp_id) {
            const existing = mpMap.get(c.mp_id);
            if (existing) {
              existing.count++;
            } else {
              mpMap.set(c.mp_id, { mp_name: c.mp_name || 'Unknown', party: c.party || '', count: 1 });
            }
          }
        }
        const topMps = Array.from(mpMap.entries())
          .map(([mp_id, data]) => ({ mp_id, ...data }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 10);

        setStats({
          ministry,
          total_contributions: resp.total_records,
          unique_mps: mpMap.size,
          top_mps: topMps,
          contributions: contribs.slice(0, 50),
        });
        setError(null);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load ministry data');
        setLoading(false);
      });
  }, [name]);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>
          Loading ministry data…
        </span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ ...mono, fontSize: 12, color: 'var(--accent-red)' }}>
          {error || 'Ministry not found.'}
        </span>
      </div>
    );
  }

  return (
    <div style={{ padding: 24, maxWidth: 900 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <span style={{
          ...mono, fontSize: 10, color: 'var(--text-tertiary)',
          textTransform: 'uppercase', letterSpacing: '0.08em',
        }}>
          MINISTRY PROFILE
        </span>
        <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 6px 0', lineHeight: 1.3 }}>
          {stats.ministry}
        </h1>

        {/* Summary stats row */}
        <div style={{ display: 'flex', gap: 24, marginTop: 8 }}>
          <div>
            <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block' }}>
              Total Matters
            </span>
            <span style={{ ...mono, fontSize: 22, fontWeight: 700, color: 'var(--accent-blue)', lineHeight: 1.2 }}>
              {stats.total_contributions}
            </span>
          </div>
          <div>
            <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block' }}>
              MPs Involved
            </span>
            <span style={{ ...mono, fontSize: 22, fontWeight: 700, color: 'var(--accent-green)', lineHeight: 1.2 }}>
              {stats.unique_mps}
            </span>
          </div>
          {stats.top_mps[0] && (
            <div>
              <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block' }}>
                Most Active MP
              </span>
              <span
                onClick={() => navigate(`/mp/${stats.top_mps[0].mp_id}`)}
                style={{ fontSize: 14, fontWeight: 600, color: 'var(--accent-amber)', cursor: 'pointer', lineHeight: 1.2 }}
              >
                {stats.top_mps[0].mp_name}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Two-column layout: Top MPs + Recent Contributions */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        {/* Top MPs */}
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 16 }}>
          <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 12 }}>
            Top MPs
          </span>
          {stats.top_mps.map((mp, i) => (
            <div
              key={mp.mp_id}
              onClick={() => navigate(`/mp/${mp.mp_id}`)}
              style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '8px 0', cursor: 'pointer',
                borderBottom: i < stats.top_mps.length - 1 ? '1px solid var(--border-subtle)' : 'none',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', minWidth: 16 }}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <div>
                  <span style={{ fontSize: 12, color: 'var(--accent-blue)', fontWeight: 500, display: 'block' }}>
                    {mp.mp_name}
                  </span>
                  {mp.party && (
                    <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                      {mp.party}
                    </span>
                  )}
                </div>
              </div>
              <span style={{ ...mono, fontSize: 13, fontWeight: 600, color: 'var(--accent-blue)' }}>
                {mp.count}
              </span>
            </div>
          ))}
          {stats.top_mps.length === 0 && (
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>No MP data available.</span>
          )}
        </div>

        {/* Recent Contributions */}
        <div>
          <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 12 }}>
            Recent Matters
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
                No contributions found for this ministry.
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

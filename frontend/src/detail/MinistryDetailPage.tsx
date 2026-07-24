import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';
import { Contribution } from '../dashboard/types';
import { typeLabel } from '../dashboard/styles';

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
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading ministry data…
        </span>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {error || 'Ministry not found.'}
        </span>
        <div style={{ marginTop: 12 }}>
          <span onClick={() => navigate('/feed')} style={{ color: 'var(--accent-blue)', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            ← Back to feed
          </span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Breadcrumb */}
      <div style={{ marginBottom: 16, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>
        <span onClick={() => navigate('/')} style={{ cursor: 'pointer', color: 'var(--accent-blue)' }}>Home</span>
        <span style={{ margin: '0 6px' }}>→</span>
        <span>Ministry</span>
        <span style={{ margin: '0 6px' }}>→</span>
        <span>{stats.ministry}</span>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)',
          textTransform: 'uppercase', letterSpacing: '0.08em',
        }}>
          MINISTRY PROFILE
        </span>
        <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
          {stats.ministry}
        </h1>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
          {stats.total_contributions} contribution{stats.total_contributions === 1 ? '' : 's'} · {stats.unique_mps} MP{stats.unique_mps === 1 ? '' : 's'} involved
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: 16, marginBottom: 24 }}>
        {/* Top MPs sidebar */}
        <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 14 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Top MPs Addressing This Ministry
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 10 }}>
            {stats.top_mps.map((mp, i) => (
              <div
                key={mp.mp_id}
                onClick={() => navigate(`/mp/${mp.mp_id}`)}
                style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '6px 8px', cursor: 'pointer', borderBottom: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', minWidth: 16 }}>
                    {i + 1}.
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--accent-blue)', fontWeight: 500 }}>{mp.mp_name}</span>
                  {mp.party && (
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                      {mp.party}
                    </span>
                  )}
                </div>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, color: 'var(--accent-blue)' }}>
                  {mp.count}
                </span>
              </div>
            ))}
            {stats.top_mps.length === 0 && (
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>No MP data available.</span>
            )}
          </div>
        </div>

        {/* Stats cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <StatCard label="Total Contributions" value={String(stats.total_contributions)} color="var(--accent-blue)" />
          <StatCard label="Unique MPs" value={String(stats.unique_mps)} color="var(--accent-green)" />
          <StatCard label="Top Contributor" value={stats.top_mps[0]?.mp_name || '—'} color="var(--accent-amber)" />
        </div>
      </div>

      {/* Recent contributions */}
      <div>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 10 }}>
          Recent Contributions
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
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)', padding: 12 }}>No contributions found for this ministry.</span>
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

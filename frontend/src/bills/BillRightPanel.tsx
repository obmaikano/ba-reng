import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { get } from '../api';
import { mono } from '../dashboard/styles';

interface BillGroup {
  bill_key: string;
  bill_name: string;
  latest_date: string;
  ministry_addressed: string | null;
  sponsor_mp_id: number | null;
  sponsor_name: string | null;
  contribution_count: number;
  stages: string[];
  latest_stage: string | null;
}

interface BillsResponse {
  total_records: number;
  returned_records: number;
  data: BillGroup[];
}

const sectionHeader: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: 'var(--text-primary)',
  textTransform: 'uppercase' as const,
  letterSpacing: '0.05em',
  margin: 0,
};

export default function BillRightPanel() {
  const [bills, setBills] = useState<BillGroup[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    get<BillsResponse>('/api/v1/bills?limit=50')
      .then((resp) => { if (!cancelled && !('error' in resp)) setBills(resp.data); })
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  const ministries = Array.from(
    new Set(bills.map((b) => b.ministry_addressed).filter((m): m is string => Boolean(m))),
  ).sort();

  const sponsors = Array.from(
    new Set(
      bills
        .map((b) => b.sponsor_name)
        .filter((n): n is string => Boolean(n))
        .map((n) => n.replace(/^HON\.\s*/, '').replace(/,\s*MP\.?$/, '')),
    ),
  );

  const totalContributions = bills.reduce((sum, b) => sum + b.contribution_count, 0);

  const stageCounts: Record<string, number> = {};
  for (const b of bills) {
    for (const s of b.stages) {
      stageCounts[s] = (stageCounts[s] ?? 0) + 1;
    }
  }

  return (
    <div>
      <div style={{ padding: 16, borderBottom: '1px solid var(--border-default)' }}>
        <h3 style={sectionHeader}>Bill Tracker</h3>
        <p style={{ fontSize: 11, color: 'var(--text-tertiary)', lineHeight: 1.4, margin: '6px 0 0 0' }}>
          {bills.length} bills · {totalContributions} records · {ministries.length} ministries
        </p>
      </div>

      {ministries.length > 0 && (
        <div style={{ padding: 16, borderBottom: '1px solid var(--border-subtle)' }}>
          <h3 style={{ ...sectionHeader, marginBottom: 8 }}>Sponsoring Ministries</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {ministries.slice(0, 10).map((m) => {
              const count = bills.filter((b) => b.ministry_addressed === m).length;
              return (
                <div key={m} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span
                    style={{ fontSize: 11, color: 'var(--text-secondary)', cursor: 'pointer' }}
                    onClick={() => navigate(`/ministry/${encodeURIComponent(m)}`)}
                  >
                    {m}
                  </span>
                  <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                    {count} bill{count === 1 ? '' : 's'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {sponsors.length > 0 && (
        <div style={{ padding: 16, borderBottom: '1px solid var(--border-subtle)' }}>
          <h3 style={{ ...sectionHeader, marginBottom: 8 }}>Bill Sponsors</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {sponsors.slice(0, 10).map((name) => {
              const count = bills.filter((b) => {
                const sponsor = (b.sponsor_name || '').replace(/^HON\.\s*/, '').replace(/,\s*MP\.?$/, '');
                return sponsor === name;
              }).length;
              return (
                <div key={name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{name}</span>
                  <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                    {count} bill{count === 1 ? '' : 's'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div style={{ padding: 16 }}>
        <h3 style={{ ...sectionHeader, marginBottom: 8 }}>By Stage</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {Object.entries(stageCounts).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([stage, count]) => (
            <div key={stage} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                {stage.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </span>
              <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

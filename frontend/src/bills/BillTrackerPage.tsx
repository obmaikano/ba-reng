import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { get } from '../api';
import { sectionTitle, mono, surface, narrativeSection } from '../dashboard/styles';

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

const STAGE_LABELS: Record<string, string> = {
  bill_presentation: 'First Reading',
  bill_1st: 'First Reading',
  bill_reading: 'Reading',
  bill_2nd: 'Second Reading',
  second_reading: 'Second Reading',
  committee_stage: 'Committee',
  bill_amendment: 'Amendments',
  amendment: 'Amendments',
  bill_3rd: 'Third Reading',
  third_reading: 'Third Reading',
};

const STAGE_COLORS: Record<string, string> = {
  bill_presentation: 'var(--accent-blue)',
  bill_1st: 'var(--accent-blue)',
  bill_reading: 'var(--accent-blue)',
  bill_2nd: 'var(--accent-amber)',
  second_reading: 'var(--accent-amber)',
  committee_stage: 'var(--accent-amber)',
  bill_amendment: 'var(--accent-red)',
  amendment: 'var(--accent-red)',
  bill_3rd: 'var(--accent-green)',
  third_reading: 'var(--accent-green)',
};

function stageBadge(stage: string) {
  return (
    <span
      key={stage}
      style={{
        ...mono,
        fontSize: 8,
        textTransform: 'uppercase',
        padding: '1px 5px',
        color: STAGE_COLORS[stage] || 'var(--text-tertiary)',
        border: `1px solid ${STAGE_COLORS[stage] || 'var(--border-subtle)'}`,
      }}
    >
      {STAGE_LABELS[stage] || stage}
    </span>
  );
}

export default function BillTrackerPage() {
  const [bills, setBills] = useState<BillGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    get<BillsResponse>('/api/v1/bills?limit=100')
      .then((resp) => {
        if (!cancelled) {
          if ('error' in resp) {
            setError((resp as unknown as { error: string }).error);
          } else {
            setBills(resp.data);
          }
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load bills');
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading bills…
        </span>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {error}
        </span>
      </div>
    );
  }

  const totalContributions = bills.reduce((sum, b) => sum + b.contribution_count, 0);

  return (
    <div style={{ padding: 24 }}>
      <div style={{ ...narrativeSection, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <span style={{ ...sectionTitle, marginBottom: 4 }}>BILLS</span>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
            Bill Tracker
          </h1>
          <p style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
            {bills.length} bills · {totalContributions} parliamentary records across all stages
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 16 }}>
        {bills.map((bill) => (
          <div
            key={bill.bill_key}
            onClick={() => navigate(`/bills/${encodeURIComponent(bill.bill_key)}`)}
            style={{
              ...surface,
              padding: '14px 16px',
              borderLeft: `3px solid ${STAGE_COLORS[bill.latest_stage || ''] || 'var(--accent-blue)'}`,
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 6 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, flexWrap: 'wrap' }}>
                  <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                    {bill.bill_key}
                  </span>
                </div>
                <h3 style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', margin: '4px 0 2px 0', lineHeight: 1.4 }}>
                  {bill.bill_name}
                </h3>
              </div>
              <span style={{ ...mono, fontSize: 12, fontWeight: 700, color: 'var(--accent-blue)', flexShrink: 0, marginLeft: 12 }}>
                {bill.contribution_count}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
              <div style={{ display: 'flex', gap: 4 }}>
                {bill.stages.map(stageBadge)}
              </div>
              {bill.sponsor_name && (
                <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
                  {bill.sponsor_name}
                </span>
              )}
              {bill.ministry_addressed && (
                <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                  {bill.ministry_addressed}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {bills.length === 0 && (
        <div style={{ padding: 12, ...surface, ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>
          No bills found.
        </div>
      )}
    </div>
  );
}

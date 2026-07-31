import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';
import { mono } from '../dashboard/styles';

interface TimelineStage {
  stage: string;
  count: number;
  first_date: string;
  last_date: string;
  items: BillContribution[];
}

interface BillContribution {
  id: number;
  subject_text: string;
  contribution_type: string;
  date: string;
  ministry_addressed: string | null;
  mp_id: number | null;
  mp_name: string | null;
  party: string | null;
  constituency: string | null;
  raw_match_name: string | null;
  doc_source_url: string | null;
}

interface BillDetail {
  bill_key: string;
  bill_name: string;
  ministry_addressed: string | null;
  sponsor_mp_id: number | null;
  total_contributions: number;
  timeline: TimelineStage[];
}

const STAGE_LABELS: Record<string, string> = {
  bill_presentation: 'First Reading',
  bill_1st: 'First Reading',
  bill_reading: 'Reading',
  bill_2nd: 'Second Reading',
  second_reading: 'Second Reading',
  committee_stage: 'Committee Stage',
  bill_amendment: 'Amendments',
  amendment: 'Amendments',
  bill_3rd: 'Third Reading',
  third_reading: 'Third Reading',
};

const STAGE_ICONS: Record<string, string> = {
  bill_presentation: '📋',
  bill_1st: '📋',
  bill_reading: '📖',
  bill_2nd: '📖',
  second_reading: '📖',
  committee_stage: '🔍',
  bill_amendment: '✏️',
  amendment: '✏️',
  bill_3rd: '✅',
  third_reading: '✅',
};

function stageColor(stage: string): string {
  if (stage.includes('3rd') || stage.includes('third')) return 'var(--accent-green)';
  if (stage.includes('2nd') || stage.includes('second')) return 'var(--accent-amber)';
  if (stage.includes('committee')) return 'var(--accent-amber)';
  if (stage.includes('amendment')) return 'var(--accent-red)';
  return 'var(--accent-blue)';
}

export default function BillDetailPage() {
  const { billKey } = useParams();
  const navigate = useNavigate();
  const [bill, setBill] = useState<BillDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!billKey) return;
    setLoading(true);
    get<BillDetail>(`/api/v1/bills/${encodeURIComponent(billKey)}`)
      .then((data) => {
        if ('error' in data) {
          setError((data as unknown as { error: string }).error);
        } else {
          setBill(data);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load bill');
        setLoading(false);
      });
  }, [billKey]);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>
          Loading bill details…
        </span>
      </div>
    );
  }

  if (error || !bill) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ ...mono, fontSize: 12, color: 'var(--accent-red)' }}>
          {error || 'Bill not found.'}
        </span>
        <div style={{ marginTop: 12 }}>
          <span onClick={() => navigate('/bills')} style={{ ...mono, fontSize: 11, color: 'var(--accent-blue)', cursor: 'pointer' }}>
            ← Back to bills
          </span>
        </div>
      </div>
    );
  }

  const dateStr = (d: string) => new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <div style={{ padding: 24, maxWidth: 900 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          BILL DETAIL
        </span>
        <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 6px 0', lineHeight: 1.3 }}>
          {bill.bill_name}
        </h1>
        <div style={{ display: 'flex', gap: 16, marginTop: 6, ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
          <span>{bill.bill_key}</span>
          {bill.ministry_addressed && (
            <>
              <span>·</span>
              <span
                onClick={() => navigate(`/ministry/${encodeURIComponent(bill.ministry_addressed!)}`)}
                style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}
              >
                {bill.ministry_addressed}
              </span>
            </>
          )}
          <span>·</span>
          <span>{bill.total_contributions} record{bill.total_contributions === 1 ? '' : 's'}</span>
        </div>
      </div>

      {/* Timeline */}
      <div style={{ marginBottom: 24 }}>
        <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 12 }}>
          Legislative Timeline
        </span>

        <div style={{ position: 'relative', paddingLeft: 24 }}>
          {/* Vertical line */}
          <div style={{
            position: 'absolute', left: 7, top: 8, bottom: 8,
            width: 2, background: 'var(--border-default)',
          }} />

          {bill.timeline.map((stage, i) => {
            const color = stageColor(stage.stage);
            const isLast = i === bill.timeline.length - 1;

            return (
              <div key={stage.stage} style={{ position: 'relative', marginBottom: isLast ? 0 : 20 }}>
                {/* Dot */}
                <div style={{
                  position: 'absolute', left: -20, top: 6,
                  width: 12, height: 12, borderRadius: '50%',
                  background: color, border: '2px solid var(--bg-canvas)',
                  zIndex: 1,
                }} />

                {/* Stage header */}
                <div style={{
                  background: 'var(--bg-elevated)', border: `1px solid var(--border-subtle)`,
                  borderLeft: `3px solid ${color}`, padding: '12px 14px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                      {STAGE_ICONS[stage.stage] || '📄'} {STAGE_LABELS[stage.stage] || stage.stage}
                    </span>
                    <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                      {stage.count} record{stage.count === 1 ? '' : 's'}
                    </span>
                  </div>
                  <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                    {dateStr(stage.first_date)}
                    {stage.first_date !== stage.last_date && ` → ${dateStr(stage.last_date)}`}
                  </span>

                  {/* Stage items */}
                  {stage.items.length <= 5 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 8 }}>
                      {stage.items.map((item) => (
                        <div
                          key={item.id}
                          onClick={() => navigate(`/contribution/${item.id}`)}
                          style={{
                            background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                            padding: '8px 10px', cursor: 'pointer',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                            <span style={{ ...mono, fontSize: 8, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                              {dateStr(item.date)}
                            </span>
                            {item.mp_name && (
                              <span
                                onClick={(e) => { e.stopPropagation(); navigate(`/mp/${item.mp_id}`); }}
                                style={{ ...mono, fontSize: 9, color: 'var(--accent-blue)', cursor: 'pointer' }}
                              >
                                {item.mp_name}
                              </span>
                            )}
                          </div>
                          <span style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4, display: 'block' }}>
                            {item.subject_text.slice(0, 200)}{item.subject_text.length > 200 ? '…' : ''}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div style={{ marginTop: 8 }}>
                      <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                        {stage.count} individual records in this stage.
                      </span>
                      {/* Show first 3 */}
                      {stage.items.slice(0, 3).map((item) => (
                        <div
                          key={item.id}
                          onClick={() => navigate(`/contribution/${item.id}`)}
                          style={{
                            background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
                            padding: '6px 10px', cursor: 'pointer', marginTop: 4,
                          }}
                        >
                          <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)' }}>
                            {dateStr(item.date)}
                          </span>
                          <span style={{ fontSize: 11, color: 'var(--text-secondary)', marginLeft: 8 }}>
                            {item.subject_text.slice(0, 120)}…
                          </span>
                        </div>
                      ))}
                      {stage.count > 3 && (
                        <span style={{ ...mono, fontSize: 9, color: 'var(--text-tertiary)', display: 'block', marginTop: 4 }}>
                          +{stage.count - 3} more records
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Back link */}
      <div style={{ marginTop: 24 }}>
        <span onClick={() => navigate('/bills')} style={{ ...mono, fontSize: 11, color: 'var(--accent-blue)', cursor: 'pointer' }}>
          ← All bills
        </span>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { get } from '../api';
import { sectionTitle, mono, surface, narrativeSection } from '../dashboard/styles';

interface BillItem {
  id: number;
  subject_text: string;
  date: string;
  raw_match_name: string;
  ministry_addressed: string;
  mp_name: string | null;
  mp_party: string | null;
}

export default function BillTrackerPage() {
  const [bills, setBills] = useState<BillItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    get<BillItem[]>('/api/v1/contributions?type=bill_presentation&limit=50')
      .then((data) => { if (!cancelled) { setBills(data); setLoading(false); } })
      .catch(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading bills...
        </span>
      </div>
    );
  }

  const sorted = [...bills].sort((a, b) => b.date.localeCompare(a.date));

  return (
    <div style={{ padding: 24 }}>
      <div style={{ ...narrativeSection, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <span style={{ ...sectionTitle, marginBottom: 4 }}>LEGISLATION</span>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
            Bills & Legislation Tracker
          </h1>
          <p style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
            Track bills through readings, committee stages, and assent
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {sorted.map((b) => {
          const sponsor = b.mp_name || b.raw_match_name || '';
          const shortSponsor = sponsor.replace(/^HON\.\s*/, '').replace(/,\s*MP\.?$/, '');

          return (
            <div
              key={b.id}
              style={{
                ...surface,
                padding: '14px 16px',
                borderLeft: '3px solid var(--accent-green)',
                cursor: 'default',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 6 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{
                      ...mono, fontSize: 9, textTransform: 'uppercase', padding: '2px 6px',
                      color: 'var(--accent-green)', border: '1px solid var(--accent-green)',
                    }}>
                      PRESENTED
                    </span>
                  </div>
                  <h3 style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
                    {b.subject_text}
                  </h3>
                </div>
                <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', flexShrink: 0, marginLeft: 12 }}>
                  {b.ministry_addressed ? `Sponsor: ${b.ministry_addressed}` : ''}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                <span>Introduced: {b.date}</span>
                {shortSponsor && <><span>&middot;</span><span>{shortSponsor}</span></>}
                {b.mp_party && <><span>&middot;</span><span>{b.mp_party}</span></>}
              </div>
            </div>
          );
        })}
      </div>

      {sorted.length === 0 && (
        <div style={{ padding: 12, ...surface, ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>
          No bills found. Check the data pipeline.
        </div>
      )}
    </div>
  );
}

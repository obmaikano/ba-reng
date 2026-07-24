import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';
import { Contribution } from '../dashboard/types';
import { typeLabel } from '../dashboard/styles';

export default function ContributionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [contribution, setContribution] = useState<Contribution | null>(null);
  const [related, setRelated] = useState<Contribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    get<Contribution>(`/api/v1/contributions/${id}`)
      .then((c) => {
        setContribution(c);
        setError(null);
        // Fetch related contributions — same ministry, same MP, recent
        const params: string[] = ['limit=10'];
        if (c.ministry_addressed) params.push(`ministry=${encodeURIComponent(c.ministry_addressed)}`);
        return get<{ data: Contribution[] }>(`/api/v1/contributions?${params.join('&')}`);
      })
      .then((resp) => {
        if (resp?.data) {
          setRelated(resp.data.filter((r) => r.id !== Number(id)).slice(0, 8));
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load contribution');
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading contribution…
        </span>
      </div>
    );
  }

  if (error || !contribution) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {error || 'Contribution not found.'}
        </span>
        <div style={{ marginTop: 12 }}>
          <span onClick={() => navigate('/feed')} style={{ color: 'var(--accent-blue)', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            ← Back to feed
          </span>
        </div>
      </div>
    );
  }

  const date = new Date(contribution.date);
  const dateStr = date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  const timeStr = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });
  const cType = contribution.contribution_type;
  const isBill = cType.startsWith('bill_');

  return (
    <div style={{ padding: 24 }}>
      {/* Breadcrumb */}
      <div style={{ marginBottom: 16, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>
        <span onClick={() => navigate('/feed')} style={{ cursor: 'pointer', color: 'var(--accent-blue)' }}>Feed</span>
        <span style={{ margin: '0 6px' }}>→</span>
        <span>Contribution #{id}</span>
      </div>

      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.05em',
            padding: '3px 8px', color: isBill ? 'var(--accent-green)' : 'var(--accent-blue)',
            border: `1px solid ${isBill ? 'var(--accent-green)' : 'var(--accent-blue)'}`,
            background: isBill ? 'rgba(22,163,74,0.1)' : 'rgba(45,127,249,0.1)',
          }}>
            {typeLabel(cType)}
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>
            ID: {contribution.id}
          </span>
        </div>
        <h1 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: '8px 0 4px 0', lineHeight: 1.4 }}>
          {contribution.subject_text}
        </h1>
      </div>

      {/* Metadata grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
        gap: 12, marginBottom: 20,
        background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 14,
      }}>
        <MetaField label="Date" value={`${dateStr} at ${timeStr}`} />
        <MetaField label="Type" value={typeLabel(cType)} />
        <MetaField label="Ministry" value={contribution.ministry_addressed || 'Unspecified'} isLink onClick={() => {
          if (contribution.ministry_addressed) navigate(`/ministry/${encodeURIComponent(contribution.ministry_addressed)}`);
        }} />
        <MetaField label="MP" value={contribution.mp_name || contribution.raw_match_name || 'Unknown'} isLink onClick={() => {
          if (contribution.mp_id) navigate(`/mp/${contribution.mp_id}`);
        }} />
        <MetaField label="Party" value={contribution.party || '—'} />
        <MetaField label="Constituency" value={contribution.constituency || '—'} isLink onClick={() => {
          if (contribution.constituency) navigate(`/constituency/${encodeURIComponent(contribution.constituency)}`);
        }} />
      </div>

      {/* Source document */}
      {contribution.source_url && (
        <div style={{
          marginBottom: 24, padding: 14,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
          borderLeft: '3px solid var(--accent-blue)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Source Document
            </span>
          </div>
          <a
            href={contribution.source_url}
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'block', marginTop: 6, fontFamily: 'var(--font-mono)', fontSize: 11,
              color: 'var(--accent-blue)', textDecoration: 'none', wordBreak: 'break-all',
            }}
          >
            {contribution.source_url}
          </a>
        </div>
      )}

      {/* Full subject text */}
      <div style={{
        marginBottom: 24, padding: 16,
        background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
      }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Full Text
        </span>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '8px 0 0 0', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
          {contribution.subject_text}
        </p>
      </div>

      {/* Related contributions */}
      {related.length > 0 && (
        <div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 10 }}>
            Related Contributions
            {contribution.ministry_addressed && <span style={{ marginLeft: 6, color: 'var(--text-tertiary)' }}>· {contribution.ministry_addressed}</span>}
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {related.map((r) => (
              <div
                key={r.id}
                onClick={() => navigate(`/contribution/${r.id}`)}
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
                  {typeLabel(r.contribution_type)}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-secondary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {r.subject_text.slice(0, 120)}{r.subject_text.length > 120 ? '…' : ''}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                  {new Date(r.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MetaField({ label, value, isLink, onClick }: { label: string; value: string; isLink?: boolean; onClick?: () => void }) {
  return (
    <div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block' }}>
        {label}
      </span>
      <span
        onClick={onClick}
        style={{
          display: 'block', marginTop: 2, fontSize: 12, fontWeight: 500,
          color: isLink ? 'var(--accent-blue)' : 'var(--text-primary)',
          cursor: isLink ? 'pointer' : 'default',
        }}
      >
        {value}
      </span>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';
import { Contribution } from '../dashboard/types';
import { typeLabel } from '../dashboard/styles';

interface MpProfile {
  id: number;
  name: string;
  constituency: string;
  party: string;
  photo_url: string | null;
  contribution_count: number;
  breakdown_by_type: { contribution_type: string; cnt: number }[];
  participation_index: {
    participation_index: number;
    breakdown: { contribution_type: string; count: number }[];
    is_proxy: boolean;
    caveat: string;
  };
}

interface MinistryCount {
  ministry: string;
  count: number;
}

export default function MpProfilePage() {
  const { mpId } = useParams();
  const navigate = useNavigate();
  const [mp, setMp] = useState<MpProfile | null>(null);
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [ministries, setMinistries] = useState<MinistryCount[]>([]);
  const [tab, setTab] = useState<'timeline' | 'type' | 'ministries' | 'compare'>('timeline');
  const [loadError, setLoadError] = useState<'not_found' | 'other' | null>(null);

  useEffect(() => {
    if (!mpId) return;
    setMp(null);
    setLoadError(null);
    Promise.all([
      get<MpProfile>(`/api/v1/mps/${mpId}`),
      get<Contribution[]>(`/api/v1/mps/${mpId}/contributions?limit=50`),
    ]).then(([mpData, contribs]) => {
      setMp(mpData);
      setContributions(contribs);
      const byMinistry = new Map<string, number>();
      for (const c of contribs) {
        if (!c.ministry_addressed) continue;
        byMinistry.set(c.ministry_addressed, (byMinistry.get(c.ministry_addressed) ?? 0) + 1);
      }
      setMinistries(
        Array.from(byMinistry.entries())
          .map(([ministry, count]) => ({ ministry, count }))
          .sort((a, b) => b.count - a.count),
      );
    }).catch((err: unknown) => {
      const message = err instanceof Error ? err.message : '';
      setLoadError(message === 'MP not found' ? 'not_found' : 'other');
    });
  }, [mpId]);

  if (loadError === 'not_found') {
    return (
      <div style={{ padding: 24, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-tertiary)' }}>
        MP not found.{' '}
        <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }} onClick={() => navigate('/find')}>
          Find your representative →
        </span>
      </div>
    );
  }

  if (loadError === 'other') {
    return (
      <div style={{ padding: 24, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-tertiary)' }}>
        Could not load this MP's profile. Please try again later.
      </div>
    );
  }

  if (!mp) {
    return (
      <div style={{ padding: 24, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-tertiary)' }}>
        Loading…
      </div>
    );
  }

  const initials = mp.name.split(/\s+/).slice(0, 2).map(w => w[0]).join('').toUpperCase();
  const oralQuestions = mp.breakdown_by_type.find(t => t.contribution_type === 'question')?.cnt ?? 0;
  const motions = mp.breakdown_by_type.find(t => t.contribution_type === 'motion')?.cnt ?? 0;
  const bills = mp.breakdown_by_type.find(t => t.contribution_type === 'bill_presentation')?.cnt ?? 0;
  const rank = mp.participation_index.participation_index;
  const topMinistries = ministries.slice(0, 2);

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 20, paddingBottom: 24, borderBottom: '1px solid var(--border-default)' }}>
        <div style={{ width: 56, height: 56, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: 'var(--accent-blue)', border: '1px solid var(--accent-blue)', background: 'var(--bg-elevated)', flexShrink: 0 }}>
          {initials}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              {mp.name}
            </h1>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>
              MP ID: MP-{String(mp.id).padStart(3, '0')}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 4, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              {mp.constituency}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 6, height: 6, background: 'var(--accent-blue)', display: 'inline-block' }} />
              {mp.party}
            </span>
            <span>Elected: 2024</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => navigate('/compare')}
            style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 500, background: 'var(--accent-blue)', color: 'white', padding: '5px 14px', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            Compare
          </button>
          <button style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-secondary)', padding: '4px 10px', border: '1px solid var(--border-subtle)', background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            Share
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: 12, marginTop: 16, marginBottom: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderLeft: '3px solid var(--accent-blue)' }}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 2, flexShrink: 0 }}><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>
        <div>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-blue)' }}>Session Focus</span>
          <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2, marginBottom: 0, lineHeight: 1.5 }}>
            {mp.name} has concentrated on{' '}
            {topMinistries.map((m, i) => (
              <span key={m.ministry}>
                <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{m.ministry} ({m.count} contributions)</span>
                {i < topMinistries.length - 1 ? ' and ' : '. '}
              </span>
            ))}
            {oralQuestions > motions ? 'Questions' : 'Motions'} dominate his record — {bills} bill reading{bills === 1 ? '' : 's'}.{' '}
            He has raised matters with {ministries.length} ministr{ministries.length === 1 ? 'y' : 'ies'} this session.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 24 }}>
        <StatCard label="Total Contributions" value={String(mp.contribution_count)} valueColor="var(--accent-blue)" />
        <StatCard label="Oral Questions" value={String(oralQuestions)} />
        <StatCard label="Motions" value={String(motions)} />
        <StatCard label="Bills" value={String(bills)} />
        <div style={{ border: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)', padding: 12, borderColor: 'rgba(245,166,35,0.3)' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Participation Rank</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 600, color: 'var(--accent-amber)', lineHeight: 1.1, marginTop: 2, display: 'flex', alignItems: 'center', gap: 8 }}>
            #{Math.round(rank)}
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', fontWeight: 400 }}>of 69</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: 12, marginBottom: 16, background: 'var(--bg-elevated)', border: '1px solid rgba(245,166,35,0.2)' }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 2, flexShrink: 0 }}>
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: 0 }}>
          <span style={{ color: 'var(--accent-amber)', fontWeight: 600 }}>Proxy Metric:</span> All counts from recorded contributions only. Botswana Parliament does not publish attendance data.
        </p>
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-default)', marginBottom: 16 }}>
        {(['timeline', 'type', 'ministries', 'compare'] as const).map((t) => (
          <span
            key={t}
            onClick={() => setTab(t)}
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              padding: '6px 14px',
              color: tab === t ? 'var(--accent-blue)' : 'var(--text-secondary)',
              borderBottom: tab === t ? '2px solid var(--accent-blue)' : '2px solid transparent',
              cursor: 'pointer',
            }}
          >
            {t === 'timeline' ? 'Timeline' : t === 'type' ? 'By Type' : t === 'ministries' ? 'Ministries' : 'Compare'}
          </span>
        ))}
      </div>

      {tab === 'timeline' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {contributions.slice(0, 15).map((c) => {
            const tagColors: Record<string, string> = { question: 'var(--accent-blue)', oral_question: 'var(--accent-blue)', motion: 'var(--accent-amber)', bill_2nd: 'var(--accent-green)', bill_presentation: 'var(--accent-green)' };
            const dotColor = tagColors[c.contribution_type] ?? 'var(--text-secondary)';
            const date = new Date(c.date);
            return (
              <div key={c.id} style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', padding: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 64, flexShrink: 0, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', textAlign: 'right' }}>
                  {date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })}<br />
                  <span style={{ color: 'var(--text-tertiary)' }}>{date.getDate()} {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][date.getMonth()]}</span>
                </div>
                <div style={{ width: 8, height: 8, background: dotColor, flexShrink: 0 }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: dotColor, textTransform: 'uppercase', letterSpacing: '0.05em', border: `1px solid ${dotColor}`, padding: '2px 6px' }}>
                  {typeLabel(c.contribution_type)}
                </span>
                <div style={{ flex: 1, fontSize: 12, color: 'var(--text-secondary)' }}>
                  {c.subject_text.slice(0, 200)}{c.subject_text.length > 200 ? '…' : ''}
                </div>
                {c.source_url && (
                  <a href={c.source_url} target="_blank" rel="noreferrer" style={{ flexShrink: 0 }}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                  </a>
                )}
              </div>
            );
          })}
          {contributions.length === 0 && (
            <div style={{ padding: 16, textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', border: '1px solid var(--border-subtle)' }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline', marginRight: 4 }}><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              No recorded activity on this day Parliament met
              <span style={{ color: 'var(--accent-amber)', cursor: 'pointer', marginLeft: 8 }}>What does this mean?</span>
            </div>
          )}
          <div style={{ marginTop: 16, textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
            <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>Load more</span>
            <span style={{ margin: '0 8px' }}>·</span>
            <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>Export CSV</span>
            <span style={{ margin: '0 8px' }}>·</span>
            <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>View source docs</span>
          </div>
        </div>
      )}

      {tab === 'ministries' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {ministries.map((m) => (
            <div key={m.ministry} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: 12 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{m.ministry}</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)' }}>{m.count}</span>
            </div>
          ))}
          {ministries.length === 0 && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-tertiary)' }}>No ministry data available.</span>
          )}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={{ border: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)', padding: 12 }}>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 600, color: valueColor ?? 'var(--text-primary)', lineHeight: 1.1, marginTop: 2 }}>{value}</div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';
import { Contribution } from '../dashboard/types';
import { typeLabel } from '../dashboard/styles';
import ScorecardGrid from '../analytics/ScorecardGrid';

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

interface HansardUtterance {
  utterance_id: number;
  speaker_name: string;
  speech_type: string;
  speech_text: string;
  language: string;
  evidence_type: string | null;
  word_count: number | null;
  sequence_order: number;
  mp_name: string;
  party: string;
  constituency: string;
  agenda_title: string;
  agenda_category: string;
}

interface EvidenceBreakdown {
  mp_id: number;
  session_id: number;
  total_utterances: number;
  breakdown: Record<string, number>;
  empirical_pct: number;
  statutory_pct: number;
  anecdotal_pct: number;
  normative_pct: number;
}

export default function MpProfilePage() {
  const { mpId } = useParams();
  const navigate = useNavigate();
  const [mp, setMp] = useState<MpProfile | null>(null);
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [ministries, setMinistries] = useState<MinistryCount[]>([]);
  const [utterances, setUtterances] = useState<HansardUtterance[]>([]);
  const [evidence, setEvidence] = useState<EvidenceBreakdown | null>(null);
  const [debateSourceUrl, setDebateSourceUrl] = useState<string | null>(null);
  const [tab, setTab] = useState<'timeline' | 'type' | 'ministries' | 'compare' | 'debate'>('timeline');
  const [loadError, setLoadError] = useState<'not_found' | 'other' | null>(null);
  const [copied, setCopied] = useState(false);
  const [timelineLimit, setTimelineLimit] = useState(15);

  const handleLoadMore = () => setTimelineLimit(prev => prev + 15);

  const handleExportCSV = () => {
    const header = 'Date,Type,Ministry,Subject,Source URL';
    const rows = contributions.slice(0, timelineLimit).map(c => {
      const date = new Date(c.date).toISOString().slice(0, 10);
      const type = typeLabel(c.contribution_type);
      const ministry = (c.ministry_addressed || '').replace(/,/g, ';');
      const subject = (c.subject_text || '').replace(/"/g, '""').replace(/,/g, ';');
      const url = c.source_url || '';
      return `${date},"${type}","${ministry}","${subject}","${url}"`;
    });
    const csv = [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `mp-${mpId}-contributions.csv`;
    a.click();
  };

  const handleViewSources = () => {
    const urls = [...new Set(contributions.slice(0, timelineLimit).map(c => c.source_url).filter(Boolean))];
    urls.forEach(url => window.open(url as string, '_blank'));
  };

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
    // Fetch Hansard utterances for debate tab
    if (mpId) {
      const mpid = Number(mpId);
      get<{ data: HansardUtterance[] }>(`/api/v1/hansard/utterances?mp_id=${mpid}&limit=20`)
        .then(res => setUtterances(Array.isArray(res.data) ? res.data : []))
        .catch(() => setUtterances([]));
      // Fetch recent evidence breakdown from sessions endpoint
      get<Array<{ session_id: number; source_url?: string }>>('/api/v1/hansard/sessions')
        .then(sessions => {
          if (Array.isArray(sessions) && sessions.length > 0) {
            const latest = sessions[0];
            if (latest.source_url) setDebateSourceUrl(latest.source_url);
            return get<EvidenceBreakdown>(`/api/v1/hansard/evidence-breakdown/${mpid}?session_id=${latest.session_id}`);
          }
          return null;
        })
        .then(eb => { if (eb) setEvidence(eb as EvidenceBreakdown); })
        .catch(() => setEvidence(null));
    }
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
          <button
            onClick={() => {
              navigator.clipboard.writeText(window.location.href).then(() => {
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }).catch(() => {});
            }}
            style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: copied ? 'var(--accent-green)' : 'var(--text-secondary)', padding: '4px 10px', border: copied ? '1px solid var(--accent-green)' : '1px solid var(--border-subtle)', background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}>
            {copied ? (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
            ) : (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            )}
            {copied ? 'Copied!' : 'Share'}
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
            {oralQuestions > motions ? 'Questions' : 'Motions'} dominate this record — {bills} bill reading{bills === 1 ? '' : 's'}.{' '}
            Matters raised with {ministries.length} ministr{ministries.length === 1 ? 'y' : 'ies'} this session.
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

      <ScorecardGrid mpId={mp.id} />

      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: 12, marginBottom: 16, background: 'var(--bg-elevated)', border: '1px solid rgba(245,166,35,0.2)' }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 2, flexShrink: 0 }}>
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: 0 }}>
          <span style={{ color: 'var(--accent-amber)', fontWeight: 600 }}>Proxy Metric:</span> All counts from recorded contributions only. Botswana Parliament does not publish attendance data.
        </p>
      </div>

      <div style={{ display: 'flex', borderBottom: '1px solid var(--border-default)', marginBottom: 16 }}>
        {(['timeline', 'type', 'ministries', 'compare', 'debate'] as const).map((t) => (
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
            {t === 'timeline' ? 'Timeline' : t === 'type' ? 'By Type' : t === 'ministries' ? 'Ministries' : t === 'compare' ? 'Compare' : 'Debate'}
          </span>
        ))}
      </div>

      {tab === 'timeline' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {contributions.slice(0, timelineLimit).map((c) => {
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
            {contributions.length > timelineLimit ? (
              <><span onClick={handleLoadMore} style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>Load more</span>
              <span style={{ margin: '0 8px' }}>·</span></>
            ) : contributions.length > 0 && (
              <><span style={{ color: 'var(--text-tertiary)' }}>All {contributions.length} shown</span>
              <span style={{ margin: '0 8px' }}>·</span></>
            )}
            <span onClick={handleExportCSV} style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>Export CSV</span>
            <span style={{ margin: '0 8px' }}>·</span>
            <span onClick={handleViewSources} style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>View source docs</span>
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

      {tab === 'type' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {mp.breakdown_by_type
            .filter(t => t.cnt > 0)
            .sort((a, b) => b.cnt - a.cnt)
            .map((t) => {
              const maxCount = Math.max(...mp.breakdown_by_type.map(x => x.cnt), 1);
              const barWidth = Math.max((t.cnt / maxCount) * 100, 3);
              const typeColors: Record<string, string> = {
                question: 'var(--accent-blue)',
                oral_question: 'var(--accent-blue)',
                motion: 'var(--accent-amber)',
                bill_presentation: 'var(--accent-green)',
                bill_2nd: 'var(--accent-green)',
                ministerial_statement: 'var(--text-secondary)',
                committee_of_supply: 'var(--accent-amber)',
              };
              const barColor = typeColors[t.contribution_type] ?? 'var(--text-secondary)';
              return (
                <div key={t.contribution_type} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', minWidth: 120 }}>
                    {typeLabel(t.contribution_type)}
                  </span>
                  <div style={{ flex: 1, height: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', position: 'relative' }}>
                    <div style={{ height: '100%', width: `${barWidth}%`, background: barColor, opacity: 0.7 }} />
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', minWidth: 30, textAlign: 'right' }}>
                    {t.cnt}
                  </span>
                </div>
              );
            })}
          {mp.breakdown_by_type.filter(t => t.cnt > 0).length === 0 && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-tertiary)' }}>No contribution type data available.</span>
          )}
        </div>
      )}

      {tab === 'compare' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 16 }}>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Session Context
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 10 }}>
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 10, textAlign: 'center' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Contributions</span>
                <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: 'var(--accent-blue)', marginTop: 4 }}>
                  {mp.contribution_count}
                </span>
              </div>
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 10, textAlign: 'center' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Ministries</span>
                <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: 'var(--accent-blue)', marginTop: 4 }}>
                  {ministries.length}
                </span>
              </div>
              <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 10, textAlign: 'center' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Rank</span>
                <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: 'var(--accent-amber)', marginTop: 4 }}>
                  #{Math.round(rank)}
                </span>
              </div>
            </div>
          </div>
          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 16, textAlign: 'center' }}>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '0 0 12px 0', lineHeight: 1.5 }}>
              Compare {mp.name} side-by-side with another MP across contribution types, ministries addressed, and participation metrics.
            </p>
            <button
              onClick={() => navigate('/compare')}
              style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 600, background: 'var(--accent-blue)', color: 'white', padding: '8px 20px', border: 'none', cursor: 'pointer' }}>
              Open Full Comparison →
            </button>
          </div>
        </div>
      )}

      {tab === 'debate' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {evidence && evidence.empirical_pct !== undefined ? (
            <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 16 }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Debate Evidence Profile
              </span>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginTop: 10 }}>
                <EvidenceBar label="Empirical" pct={evidence.empirical_pct} color="var(--accent-green)" />
                <EvidenceBar label="Statutory" pct={evidence.statutory_pct} color="var(--accent-blue)" />
                <EvidenceBar label="Anecdotal" pct={evidence.anecdotal_pct} color="var(--accent-amber)" />
                <EvidenceBar label="Normative" pct={evidence.normative_pct} color="var(--text-secondary)" />
              </div>
            </div>
          ) : null}

          {debateSourceUrl && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 0' }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <a href={debateSourceUrl} target="_blank" rel="noreferrer" style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-blue)', textDecoration: 'none' }}>
                View source Hansard document →
              </a>
            </div>
          )}

          {utterances.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {utterances.map((u) => {
                const topicTag = u.evidence_type || u.speech_type;
                const evidenceColors: Record<string, string> = {
                  EMPIRICAL: 'var(--accent-green)',
                  STATUTORY: 'var(--accent-blue)',
                  ANECDOTAL: 'var(--accent-amber)',
                  NORMATIVE: 'var(--text-secondary)',
                };
                const tagColor = evidenceColors[u.evidence_type || ''] ?? 'var(--text-tertiary)';
                return (
                  <div key={u.utterance_id} style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', padding: 10, display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: tagColor, textTransform: 'uppercase', letterSpacing: '0.05em', border: `1px solid ${tagColor}`, padding: '1px 6px', flexShrink: 0, marginTop: 1 }}>
                      {topicTag}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {u.speech_text.slice(0, 300)}{u.speech_text.length > 300 ? '…' : ''}
                      </div>
                      <div style={{ display: 'flex', gap: 12, marginTop: 6, fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                        <span>{u.agenda_title}</span>
                        <span>·</span>
                        <span>{u.language?.toUpperCase() || 'EN'}</span>
                        {u.word_count != null && <><span>·</span><span>{u.word_count} words</span></>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ padding: 16, textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', border: '1px solid var(--border-subtle)' }}>
              No Hansard debate utterances on record for this MP.
            </div>
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

function EvidenceBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', padding: 8, textAlign: 'center' }}>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>{label}</span>
      <span style={{ display: 'block', fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700, color, marginTop: 2 }}>
        {pct}%
      </span>
    </div>
  );
}

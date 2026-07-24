import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { get } from '../api';
import { MpSummary } from '../dashboard/types';

interface CompareData {
  id: number;
  name: string;
  constituency: string;
  party: string;
  contribution_count: number;
  breakdown_by_type: { contribution_type: string; cnt: number }[];
  ministries: { ministry: string; count: number }[];
}

function generateComparisonStory(mpA: CompareData, mpB: CompareData): string {
  const leader = mpA.contribution_count >= mpB.contribution_count ? mpA : mpB;
  const follower = leader === mpA ? mpB : mpA;
  const diff = leader.contribution_count - follower.contribution_count;
  const gapPhrase = diff > 0 ? ` (a gap of ${diff})` : '';

  const leaderMotions = typeCount(leader, 'motion');
  const followerMotions = typeCount(follower, 'motion');

  if (diff === 0) {
    return `${mpA.name} and ${mpB.name} have equal activity with ${mpA.contribution_count} recorded contributions each.`;
  }

  let story = `${leader.name} leads the comparison with ${leader.contribution_count} total contributions vs ${follower.name}'s ${follower.contribution_count}${gapPhrase}. `;

  if (leaderMotions > followerMotions) {
    story += `The gap is widest in motions put forward (${leaderMotions} vs ${followerMotions}). `;
  } else if (followerMotions > leaderMotions) {
    story += `${follower.name} put forward more motions than ${leader.name} (${followerMotions} vs ${leaderMotions}). `;
  }

  const leaderQuestions = typeCount(leader, 'question') + typeCount(leader, 'oral_question');
  const followerQuestions = typeCount(follower, 'question') + typeCount(follower, 'oral_question');
  if (followerQuestions > leaderQuestions) {
    story += `However, ${follower.name} asked more questions than ${leader.name} (${followerQuestions} vs ${leaderQuestions}).`;
  }

  return story;
}

function typeCount(dp: CompareData, type: string): number {
  const exact = dp.breakdown_by_type.find(t => t.contribution_type === type)?.cnt ?? 0;
  if (exact > 0) return exact;
  if (type === 'question' || type === 'oral_question') {
    return (dp.breakdown_by_type.find(t => t.contribution_type === 'oral_question')?.cnt ?? 0)
      + (dp.breakdown_by_type.find(t => t.contribution_type === 'question')?.cnt ?? 0);
  }
  return exact;
}

function topMinistry(dp: CompareData): { ministry: string; count: number } {
  if (dp.ministries.length === 0) return { ministry: '—', count: 0 };
  return dp.ministries[0];
}

export default function ComparePage() {
  const [mps, setMps] = useState<MpSummary[]>([]);
  const [aId, setAId] = useState(0);
  const [bId, setBId] = useState(0);
  const [mpA, setMpA] = useState<CompareData | null>(null);
  const [mpB, setMpB] = useState<CompareData | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    get<MpSummary[]>('/api/v1/mps').then(setMps).catch(() => {});
  }, []);

  useEffect(() => {
    if (aId) {
      get<CompareData>(`/api/v1/mps/${aId}`)
        .then(async (mp) => {
          const contribs = await get<{ministry_addressed: string | null}[]>(`/api/v1/mps/${aId}/contributions?limit=200`);
          const byMinistry = new Map<string, number>();
          for (const c of contribs) {
            if (!c.ministry_addressed) continue;
            byMinistry.set(c.ministry_addressed, (byMinistry.get(c.ministry_addressed) ?? 0) + 1);
          }
          setMpA({ ...mp, ministries: Array.from(byMinistry.entries()).map(([ministry, count]) => ({ ministry, count })).sort((a, b) => b.count - a.count) });
        })
        .catch(() => setMpA(null));
    }
  }, [aId]);

  useEffect(() => {
    if (bId) {
      get<CompareData>(`/api/v1/mps/${bId}`)
        .then(async (mp) => {
          const contribs = await get<{ministry_addressed: string | null}[]>(`/api/v1/mps/${bId}/contributions?limit=200`);
          const byMinistry = new Map<string, number>();
          for (const c of contribs) {
            if (!c.ministry_addressed) continue;
            byMinistry.set(c.ministry_addressed, (byMinistry.get(c.ministry_addressed) ?? 0) + 1);
          }
          setMpB({ ...mp, ministries: Array.from(byMinistry.entries()).map(([ministry, count]) => ({ ministry, count })).sort((a, b) => b.count - a.count) });
        })
        .catch(() => setMpB(null));
    }
  }, [bId]);

  const selectStyle: React.CSSProperties = {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border-default)',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    padding: '5px 24px 5px 8px',
    outline: 'none',
    cursor: 'pointer',
    WebkitAppearance: 'none',
    appearance: 'none',
    backgroundImage: `url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%238B95A4' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 8px center',
    width: '100%',
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-amber)', display: 'flex', alignItems: 'center', gap: 4 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          PROXY_METRIC
        </span>
        <h1 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: 0, marginTop: 4 }}>
          Compare MPs
        </h1>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4, marginBottom: 0 }}>
          Side-by-side view of participation metrics.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        <div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 4 }}>MP A</span>
          <select value={aId} onChange={(e) => setAId(Number(e.target.value))} style={selectStyle}>
            <option value={0}>Select MP...</option>
            {mps.filter(mp => mp.id !== bId).map(mp => (
              <option key={mp.id} value={mp.id}>{mp.name} ({mp.party} · {mp.constituency})</option>
            ))}
          </select>
        </div>
        <div>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: 4 }}>MP B</span>
          <select value={bId} onChange={(e) => setBId(Number(e.target.value))} style={selectStyle}>
            <option value={0}>Select MP...</option>
            {mps.filter(mp => mp.id !== aId).map(mp => (
              <option key={mp.id} value={mp.id}>{mp.name} ({mp.party} · {mp.constituency})</option>
            ))}
          </select>
        </div>
      </div>

      {mpA && mpB && (
        <>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: 12, marginBottom: 16, background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', borderLeft: '3px solid var(--accent-blue)' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 2, flexShrink: 0 }}><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>
            <div>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-blue)' }}>Comparison Story</span>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2, marginBottom: 0, lineHeight: 1.5 }}>
                {generateComparisonStory(mpA, mpB)}
              </p>
            </div>
          </div>

          <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '4fr 4fr 4fr', borderBottom: '1px solid var(--border-subtle)' }}>
              <div style={{ padding: 12, borderRight: '1px solid var(--border-subtle)', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Metric</div>
              <div style={{ padding: 12, borderRight: '1px solid var(--border-subtle)', textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-blue)', textTransform: 'uppercase', letterSpacing: '0.08em', cursor: 'pointer' }} onClick={() => navigate(`/mp/${mpA.id}`)}>{mpA.name}</div>
              <div style={{ padding: 12, textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-blue)', textTransform: 'uppercase', letterSpacing: '0.08em', cursor: 'pointer' }} onClick={() => navigate(`/mp/${mpB.id}`)}>{mpB.name}</div>
            </div>
            {[
              { label: 'Total Contributions', a: mpA.contribution_count, b: mpB.contribution_count },
              { label: 'Questions', a: typeCount(mpA, 'oral_question'), b: typeCount(mpB, 'oral_question') },
              { label: 'Motions', a: typeCount(mpA, 'motion'), b: typeCount(mpB, 'motion') },
              { label: 'Bills', a: typeCount(mpA, 'bill_presentation'), b: typeCount(mpB, 'bill_presentation') },
              { label: 'Ministries Raised With', a: mpA.ministries.length, b: mpB.ministries.length },
              { label: 'Top Ministry', aStr: `${topMinistry(mpA).ministry} (${topMinistry(mpA).count})`, bStr: `${topMinistry(mpB).ministry} (${topMinistry(mpB).count})` },
            ].map((row, i) => {
              const isLast = i === 5;
              const aVal = 'a' in row ? String(row.a) : (row as {aStr: string}).aStr;
              const bVal = 'b' in row ? String(row.b) : (row as {bStr: string}).bStr;
              const aNum = 'a' in row ? (row.a as number) : null;
              const bNum = 'b' in row ? (row.b as number) : null;
              const aHigher = aNum !== null && bNum !== null ? aNum > bNum : false;
              const bHigher = aNum !== null && bNum !== null ? bNum > aNum : false;

              return (
                <div key={row.label} style={{ display: 'grid', gridTemplateColumns: '4fr 4fr 4fr', borderBottom: isLast ? 'none' : '1px solid var(--border-subtle)' }}>
                  <div style={{ padding: 12, borderRight: '1px solid var(--border-subtle)', fontSize: 12, color: 'var(--text-secondary)' }}>{row.label}</div>
                  <div style={{ padding: 12, borderRight: '1px solid var(--border-subtle)', textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: aNum ? 14 : 11, fontWeight: aHigher ? 600 : 400, color: aHigher ? 'var(--accent-blue)' : 'var(--text-primary)' }}>
                    {aVal}
                  </div>
                  <div style={{ padding: 12, textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: bNum ? 14 : 11, fontWeight: bHigher ? 600 : 400, color: bHigher ? 'var(--accent-blue)' : 'var(--text-primary)' }}>
                    {bVal}
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: 12, marginTop: 16, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 2, flexShrink: 0 }}><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <p style={{ fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
              This comparison uses the Participation Index, which counts some kinds of activity more than others.{' '}
              <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>Download as PDF</span>.
            </p>
          </div>
        </>
      )}

      {(!mpA || !mpB) && (
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-tertiary)' }}>
          Select two MPs to compare.
        </span>
      )}
    </div>
  );
}

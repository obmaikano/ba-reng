import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { get } from '../api';
import { MpSummary, BreakdownItem } from '../dashboard/types';
import { sectionTitle, mono } from '../dashboard/styles';

const PARTY_SHORT: Record<string, string> = {
  'Umbrella for Democratic Change (UDC)': 'UDC',
  'Botswana Democratic Party (BDP)': 'BDP',
  'Botswana Congress Party (BCP)': 'BCP',
  'Botswana Patriotic Front (BPF)': 'BPF',
};

const PARTY_COLOR: Record<string, string> = {
  'Umbrella for Democratic Change (UDC)': 'var(--accent-blue)',
  'Botswana Democratic Party (BDP)': 'var(--accent-blue)',
  'Botswana Congress Party (BCP)': 'var(--accent-amber)',
  'Botswana Patriotic Front (BPF)': 'var(--accent-green)',
};

const ROW_COLS = '36px minmax(120px, 2fr) 64px 1fr 1fr 1fr 1fr 1fr' as const;
const ROW_GAP = 12;

function shortParty(party: string): string {
  return PARTY_SHORT[party] ?? party;
}

function partyColor(party: string): string {
  return PARTY_COLOR[party] ?? 'var(--accent-blue)';
}

function downloadCSV(mps: MpSummary[]) {
  const getCount = (b: BreakdownItem[] | undefined, t: string) => b?.find((x) => x.contribution_type === t)?.count ?? 0;
  const rows = mps.map((mp, i) => {
    const b = mp.participation_index.breakdown;
    return [
      i + 1,
      mp.name,
      mp.constituency,
      shortParty(mp.party),
      mp.participation_index.participation_index,
      mp.contribution_count,
      getCount(b, 'oral_question'),
      getCount(b, 'motion'),
      getCount(b, 'committee_of_supply'),
    ].join(',');
  });
  const header = 'Rank,MP,Constituency,Party,Index Score,Total Contributions,Oral Questions,Motions,Committee of Supply';
  const blob = new Blob([`${header}\n${rows.join('\n')}`], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'participation_index.csv';
  a.click();
  URL.revokeObjectURL(url);
}

function getTypeCount(
  breakdown: BreakdownItem[] | undefined,
  type: string,
): number {
  return breakdown?.find((b) => b.contribution_type === type)?.count ?? 0;
}

function InfoIcon({ size = 12, color = 'currentColor' }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  );
}

function AlertIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="var(--accent-amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

const thRight = { ...sectionTitle, textAlign: 'right' } as const;

interface RankRowProps {
  mp: MpSummary;
  rank: number;
  maxIndex: number;
  onSelect: (id: number) => void;
}

function RankRow({ mp, rank, maxIndex, onSelect }: RankRowProps) {
  const pi = mp.participation_index;
  const score = pi.participation_index;
  const isZero = score === 0;
  const isFirst = rank === 1;
  const breakdown = pi.breakdown;
  const oralQ = getTypeCount(breakdown, 'oral_question');
  const motion = getTypeCount(breakdown, 'motion');
  const cos = getTypeCount(breakdown, 'committee_of_supply');
  const barWidth = (score / maxIndex) * 100;
  const pColor = partyColor(mp.party);

  return (
    <div
      onClick={() => onSelect(mp.id)}
      style={{
        display: 'grid', gridTemplateColumns: ROW_COLS, gap: ROW_GAP,
        padding: '10px 16px', alignItems: 'center', cursor: 'pointer',
        borderBottom: '1px solid var(--border-subtle)',
        opacity: isZero ? 0.5 : 1, transition: 'background 120ms ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--bg-elevated)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      <span style={{ ...mono, fontSize: 12, color: isFirst ? 'var(--accent-blue)' : 'var(--text-secondary)', fontWeight: isFirst ? 700 : 400 }}>
        {rank}
      </span>
      <div style={{ minWidth: 0 }}>
        <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {mp.name}
        </span>
        <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 1 }}>
          {mp.constituency}
        </span>
      </div>
      <div>
        <span style={{ ...mono, fontSize: 10, color: pColor, border: `1px solid ${pColor}`, padding: '1px 6px', display: 'inline-block' }}>
          {shortParty(mp.party)}
        </span>
      </div>
      <div style={{ textAlign: 'right' }}>
        <span style={{ ...mono, fontSize: 13, fontWeight: 600, color: isZero ? 'var(--accent-amber)' : 'var(--accent-blue)' }}>
          {score}
        </span>
        {!isZero && (
          <div style={{ height: 2, background: 'var(--bg-elevated)', marginTop: 2 }}>
            <div style={{ height: 2, background: 'var(--accent-blue)', width: `${barWidth}%` }} />
          </div>
        )}
      </div>
      <span style={{ ...mono, fontSize: 12, textAlign: 'right', color: 'var(--text-secondary)' }}>{mp.contribution_count}</span>
      <span style={{ ...mono, fontSize: 12, textAlign: 'right', color: 'var(--text-primary)' }}>{oralQ}</span>
      <span style={{ ...mono, fontSize: 12, textAlign: 'right', color: 'var(--text-primary)' }}>{motion}</span>
      <span style={{ ...mono, fontSize: 12, textAlign: 'right', color: 'var(--text-primary)' }}>{cos}</span>
    </div>
  );
}

export default function RankingsPage() {
  const navigate = useNavigate();
  const [mps, setMps] = useState<MpSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [partyFilter, setPartyFilter] = useState('All');

  useEffect(() => {
    let cancelled = false;
    get<MpSummary[]>('/api/v1/mps')
      .then((data) => { if (!cancelled) { setMps(data); setLoading(false); } })
      .catch(() => { if (!cancelled) { setError(true); setLoading(false); } });
    return () => { cancelled = true; };
  }, []);

  const parties = useMemo(() => {
    const unique = new Set(mps.map((m) => m.party).filter(Boolean));
    return ['All', ...Array.from(unique).sort()];
  }, [mps]);

  const sorted = useMemo(
    () => [...mps].sort((a, b) => b.participation_index.participation_index - a.participation_index.participation_index),
    [mps],
  );

  const filtered = useMemo(
    () => (partyFilter === 'All' ? sorted : sorted.filter((m) => m.party === partyFilter)),
    [sorted, partyFilter],
  );

  const maxIndex = useMemo(
    () => Math.max(1, ...sorted.map((m) => m.participation_index.participation_index)),
    [sorted],
  );

  const zeroCount = sorted.filter((m) => m.participation_index.participation_index === 0).length;
  const totalMps = sorted.length;

  if (error) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Could not load the rankings. Please try again later.
        </span>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading participation index…
        </span>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <span style={{ ...mono, fontSize: 10, color: 'var(--accent-amber)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <InfoIcon color="var(--accent-amber)" /> PROXY_METRIC
          </span>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
            Participation Index
          </h1>
          <p style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
            Ranked by recorded contributions &middot; 13th Parliament, 5th Session
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={() => downloadCSV(filtered)}
            style={{ ...mono, fontSize: 11, color: 'var(--text-secondary)', background: 'transparent', border: '1px solid var(--border-default)', padding: '4px 10px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <DownloadIcon /> CSV
          </button>
          <select
            value={partyFilter}
            onChange={(e) => setPartyFilter(e.target.value)}
            style={{
              ...mono, fontSize: 11, color: 'var(--text-secondary)', background: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)', padding: '4px 8px', cursor: 'pointer',
              minWidth: 130, appearance: 'none', WebkitAppearance: 'none',
              backgroundImage: 'url("data:image/svg+xml;charset=utf-8,<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'10\' height=\'6\'><path d=\'M0 0l5 6 5-6z\' fill=\'%235A6473\'/></svg>")',
              backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center', paddingRight: 28,
            }}
          >
            {parties.map((p) => (
              <option key={p} value={p}>{p === 'All' ? 'All Parties' : shortParty(p)}</option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: 12, marginBottom: 24, background: 'var(--bg-elevated)', border: '1px solid rgba(245,166,35,0.2)' }}>
        <AlertIcon />
        <div>
          <h4 style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-amber)', margin: '0 0 4px 0' }}>
            Proxy Metric — Not Attendance Data
          </h4>
          <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
            This index reflects{' '}
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>RECORDED_CONTRIBUTIONS</span>{' '}
            only. Botswana Parliament keeps no attendance register.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: ROW_COLS, gap: ROW_GAP, padding: '8px 16px', borderBottom: '1px solid var(--border-default)', background: 'var(--bg-surface)' }}>
        <div style={sectionTitle}>#</div>
        <div style={sectionTitle}>MP</div>
        <div style={sectionTitle}>Party</div>
        <div style={thRight}>Index</div>
        <div style={thRight}>Total</div>
        <div style={thRight}>Questions</div>
        <div style={thRight}>Motions</div>
        <div style={thRight} title="Committee of Supply — budget review sessions" aria-label="Committee of Supply column — budget review sessions">Budget</div>
      </div>

      {filtered.map((mp, idx) => (
        <RankRow key={mp.id} mp={mp} rank={idx + 1} maxIndex={maxIndex} onSelect={(id) => navigate(`/mp/${id}`)} />
      ))}

      {zeroCount > 0 && (
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: 12, marginTop: 8, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
          <InfoIcon size={14} color="var(--accent-amber)" />
          <p style={{ fontSize: 11, color: 'var(--text-tertiary)', margin: 0, lineHeight: 1.5 }}>
            {zeroCount} of {totalMps} MPs have zero recorded contributions. Zero recorded does not mean absent.
          </p>
        </div>
      )}
    </div>
  );
}

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { get } from '../api';
import { MpSummary } from '../dashboard/types';

interface ApiConstituency {
  constituency: string;
  mp_name: string;
  party: string;
  contribution_count: number;
}

interface ResolvedConstituency {
  constituency: string;
  mp_name: string;
  mp_id: number | null;
  party: string;
  contribution_count: number;
}

function ResultCard({ c }: { c: ResolvedConstituency }) {
  const navigate = useNavigate();
  const [hover, setHover] = useState(false);

  const initials = c.mp_name
    ? c.mp_name.split(/\s+/).slice(0, 2).map(w => w[0]).join('').toUpperCase()
    : '??';

  return (
    <div
      onClick={() => {
        if (c.mp_id) navigate(`/mp/${c.mp_id}`);
      }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: hover ? 'var(--bg-hover)' : 'var(--bg-elevated)',
        border: '1px solid var(--border-default)',
        padding: 12,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        cursor: c.mp_id ? 'pointer' : 'default',
        transition: 'background 0.1s',
      }}
    >
      <div
        style={{
          width: 40,
          height: 40,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'var(--font-mono)',
          fontSize: 14,
          fontWeight: 600,
          border: '1px solid var(--border-default)',
          background: 'var(--bg-elevated)',
          color: 'var(--text-primary)',
          flexShrink: 0,
        }}
      >
        {initials}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text-primary)' }}>
          {c.mp_name}
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
          {c.constituency.toUpperCase().replace(/\s+/g, '_')} · {c.party} · {c.contribution_count} contributions this session
        </div>
      </div>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--accent-blue)', textTransform: 'uppercase', letterSpacing: '0.05em', border: '1px solid rgba(45,127,249,0.3)', background: 'rgba(45,127,249,0.1)', padding: '2px 6px' }}>
        ORAL_Q: {Math.floor(Math.random() * 50) + 1}
      </span>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--accent-amber)', textTransform: 'uppercase', letterSpacing: '0.05em', border: '1px solid rgba(245,166,35,0.3)', background: 'rgba(245,166,35,0.1)', padding: '2px 6px' }}>
        MOTION: {Math.floor(Math.random() * 15) + 1}
      </span>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
    </div>
  );
}

export default function FindMpPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [data, setData] = useState<ResolvedConstituency[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      get<ApiConstituency[]>('/api/v1/constituencies'),
      get<MpSummary[]>('/api/v1/mps'),
    ])
      .then(([constituencies, mps]) => {
        const mpByName = new Map(mps.map((mp) => [mp.name.toLowerCase(), mp.id]));
        const resolved: ResolvedConstituency[] = constituencies.map((c) => ({
          constituency: c.constituency,
          mp_name: c.mp_name,
          mp_id: mpByName.get(c.mp_name.toLowerCase()) ?? null,
          party: c.party,
          contribution_count: c.contribution_count,
        }));
        setData(resolved);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = query.trim()
    ? data.filter((c) =>
        c.constituency.toLowerCase().includes(query.toLowerCase()) ||
        c.mp_name.toLowerCase().includes(query.toLowerCase())
      )
    : [];

  const allSorted = [...data].sort((a, b) => a.constituency.localeCompare(b.constituency));

  if (loading) {
    return (
      <div style={{ padding: 24, fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-tertiary)' }}>
        Loading constituencies…
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-amber)', display: 'flex', alignItems: 'center', gap: 4, marginBottom: 8 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          FIND_YOUR_MP
        </span>
        <h1 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
          Find Your Representative
        </h1>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', marginTop: 4, marginBottom: 0 }}>
          Enter a constituency name or search by MP name.
        </p>
      </div>

      <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', padding: 16, marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <div style={{ flex: 1, position: 'relative' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }}>
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              type="text"
              placeholder="Constituency name, MP name, or party..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-default)',
                color: 'var(--text-primary)',
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                padding: '5px 8px 5px 36px',
                width: '100%',
                outline: 'none',
                boxSizing: 'border-box',
                boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.3)',
              }}
            />
          </div>
          <button
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 11,
              fontWeight: 500,
              background: 'var(--accent-blue)',
              color: 'white',
              padding: '5px 14px',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 5,
            }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            Search
          </button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>
          <span>Try: <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }} onClick={() => setQuery('Gaborone')}>Gaborone</span></span>
          <span>·</span>
          <span>Popular: <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }} onClick={() => setQuery('Francistown')}>Francistown</span></span>
          <span>·</span>
          <span style={{ cursor: 'pointer' }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ verticalAlign: 'middle', marginRight: 4 }}><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            Browse all {data.length} constituencies
          </span>
        </div>
      </div>

      {query.trim() && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Results for &ldquo;{query}&rdquo;
          </span>

          {filtered.length === 0 ? (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', padding: 16, textAlign: 'center', border: '1px solid var(--border-subtle)' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline', marginBottom: 4 }}>
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/>
              </svg>
              <p style={{ margin: 0, marginTop: 4 }}>
                No results for &ldquo;{query}&rdquo;. Check spelling or{' '}
                <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>browse all constituencies</span>.
              </p>
            </div>
          ) : (
            filtered.map((c) => (
              <ResultCard key={`${c.constituency}-${c.mp_id ?? 'unknown'}`} c={c} />
            ))
          )}
        </div>
      )}

      <div style={{ marginTop: 32, borderTop: '1px solid var(--border-subtle)', paddingTop: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            All {data.length} Constituencies
          </span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-blue)', cursor: 'pointer' }}>
            View full directory &rarr;
          </span>
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: 4,
            marginTop: 8,
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-secondary)',
          }}
        >
          {allSorted.slice(0, 9).map((c) => (
            <span
              key={c.constituency}
              onClick={() => {
                if (c.mp_id) {
                  setQuery('');
                  navigate(`/mp/${c.mp_id}`);
                }
              }}
              style={{ cursor: c.mp_id ? 'pointer' : 'default', padding: 4 }}
            >
              {c.constituency}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

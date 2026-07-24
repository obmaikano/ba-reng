import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { get } from '../api';
import { sectionTitle, mono, surface, narrativeSection, typeTag } from '../dashboard/styles';

interface SearchResult {
  id: number;
  contribution_type: string;
  subject_text: string;
  date: string;
  ministry_addressed: string | null;
  source_url: string;
  mp_name: string | null;
  party: string | null;
  constituency: string | null;
}

export default function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await get<SearchResult[]>(`/api/v1/search?q=${encodeURIComponent(q)}`);
      setResults(data);
    } catch {
      setResults([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const input = document.getElementById('search-input');
        input?.focus();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') doSearch(query);
  };

  return (
    <div style={{ padding: 24 }}>
      <div style={{ ...narrativeSection }}>
        <span style={{ ...sectionTitle, marginBottom: 4 }}>SEARCH</span>
        <h1 style={{ fontSize: 18, fontWeight: 600, color: 'var(--text-primary)', margin: '4px 0 2px 0' }}>
          Full-Text Search
        </h1>
        <p style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)', margin: 0 }}>
          Search across subjects, MP names, and ministries
        </p>
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <input
            id="search-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search contributions, MPs, ministries..."
            autoFocus
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '10px 14px 10px 36px',
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-default)',
              color: 'var(--text-primary)',
              fontFamily: 'var(--font-ui)',
              fontSize: 13,
              outline: 'none',
            }}
          />
          <svg
            width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="var(--text-tertiary)" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round"
            style={{ position: 'absolute', left: 12, top: 12 }}
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <span style={{
            position: 'absolute', right: 10, top: 10,
            ...mono, fontSize: 10, color: 'var(--text-tertiary)',
            background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)',
            padding: '1px 5px',
          }}>
            {navigator.platform.includes('Mac') ? '⌘K' : 'Ctrl+K'}
          </span>
        </div>
        <button
          onClick={() => doSearch(query)}
          style={{
            ...mono, fontSize: 12, color: 'var(--text-primary)',
            background: 'var(--accent-blue)', border: 'none',
            padding: '8px 16px', cursor: 'pointer',
          }}
        >
          Search
        </button>
      </div>

      {loading && (
        <span style={{ ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>
          Searching...
        </span>
      )}

      {!loading && searched && results.length === 0 && (
        <div style={{ ...surface, padding: 12, ...mono, fontSize: 12, color: 'var(--text-tertiary)' }}>
          No results found for "{query}".
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {results.map((r) => (
          <div
            key={r.id}
            onClick={() => r.mp_name && navigate(`/mp/${r.id}`)}
            style={{
              ...surface,
              padding: '12px 16px',
              cursor: r.mp_name ? 'pointer' : 'default',
              borderLeft: '3px solid var(--accent-blue)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={typeTag(r.contribution_type)}>{r.contribution_type.replace(/_/g, ' ')}</span>
              <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                {r.date}
              </span>
              {r.mp_name && (
                <>
                  <span style={{ color: 'var(--text-tertiary)' }}>&middot;</span>
                  <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--accent-blue)' }}>
                    {r.mp_name}
                  </span>
                  {r.party && (
                    <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                      {r.party}
                    </span>
                  )}
                  {r.constituency && (
                    <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                      {r.constituency}
                    </span>
                  )}
                </>
              )}
            </div>
            <p style={{
              fontSize: 12, color: 'var(--text-secondary)', margin: 0,
              lineHeight: 1.5, overflow: 'hidden', textOverflow: 'ellipsis',
              display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical',
            }}>
              {r.subject_text}
            </p>
            {r.ministry_addressed && (
              <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', marginTop: 4, display: 'inline-block' }}>
                {r.ministry_addressed}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

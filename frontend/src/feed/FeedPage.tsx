import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Contribution } from '../dashboard/types';
import { typeTag, typeLabel, mono } from '../dashboard/styles';

interface FeedPageProps {
  contributions: Contribution[];
  totalCount: number;
}

export default function FeedPage({ contributions, totalCount }: FeedPageProps) {
  const displayed = contributions.length;

  return (
    <div>
      <div
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 10,
          background: 'var(--bg-canvas)',
          borderBottom: '1px solid var(--border-default)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '10px 20px',
          }}
        >
          <div>
            <h2 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
              Live Activity Feed
            </h2>
            <p style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)', margin: 0, marginTop: 2 }}>
              Displaying {displayed} of {totalCount} records &mdash; 13th Parliament, 5th Session
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <button
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--text-secondary)',
                padding: '4px 10px',
                border: '1px solid var(--border-subtle)',
                background: 'transparent',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
              Filter
            </button>
            <button
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
                color: 'var(--text-secondary)',
                padding: '4px 10px',
                border: '1px solid var(--border-subtle)',
                background: 'transparent',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              CSV
            </button>
          </div>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '2fr 3fr 1.5fr 4.5fr 1fr',
          gap: 12,
          padding: '6px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'var(--bg-surface)',
          fontFamily: 'var(--font-mono)',
          fontSize: 10,
          color: 'var(--text-tertiary)',
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
        }}
      >
        <div>Timestamp</div>
        <div>MP</div>
        <div>Type</div>
        <div>Subject / Excerpt</div>
        <div style={{ textAlign: 'right' }}>Source</div>
      </div>

      {contributions.map((c) => (
        <FeedRow key={c.id} contribution={c} />
      ))}

      {displayed < totalCount && (
        <div
          style={{
            padding: 16,
            textAlign: 'center',
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            color: 'var(--text-tertiary)',
            borderTop: '1px solid var(--border-subtle)',
          }}
        >
          {displayed} of {totalCount} records &middot;{' '}
          <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>Load more &rarr;</span>
        </div>
      )}
    </div>
  );
}

function FeedRow({ contribution: c }: { contribution: Contribution }) {
  const [hover, setHover] = useState(false);

  const navigate = useNavigate();

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '2fr 3fr 1.5fr 4.5fr 1fr',
        gap: 12,
        padding: '10px 20px',
        alignItems: 'center',
        borderBottom: '1px solid var(--border-subtle)',
        cursor: c.mp_id ? 'pointer' : 'default',
        background: hover ? 'var(--bg-hover)' : 'transparent',
        transition: 'background 0.1s',
      }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onClick={() => { if (c.mp_id) navigate(`/mp/${c.mp_id}`); }}
    >
      <div>
        <div style={{ ...mono, fontSize: 12, color: 'var(--text-secondary)' }}>
          {new Date(c.date).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
        </div>
        <div style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
          {c.date}
        </div>
      </div>
      <div>
        <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>
          {c.mp_name || 'Unresolved'}
        </div>
        <div style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
          {c.constituency || '—'} · {c.party || '—'}
        </div>
      </div>
      <div>
        <span style={typeTag(c.contribution_type)}>{typeLabel(c.contribution_type)}</span>
      </div>
      <div
        style={{
          fontSize: 12,
          color: 'var(--text-secondary)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {c.subject_text}
      </div>
      <div style={{ textAlign: 'right' }}>
        {c.source_url && (
          <a
            href={c.source_url}
            target="_blank"
            rel="noreferrer"
            style={{
              ...mono,
              fontSize: 10,
              color: hover ? 'var(--accent-blue)' : 'var(--text-tertiary)',
              textDecoration: 'none',
              transition: 'color 0.1s',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </a>
        )}
      </div>
    </div>
  );
}

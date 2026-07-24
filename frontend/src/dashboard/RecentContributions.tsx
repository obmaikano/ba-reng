import { useNavigate } from 'react-router-dom';
import { Contribution } from './types';
import { narrativeSection, sectionTitle, mono, typeTag, typeLabel } from './styles';

interface RecentContributionsProps {
  contributions: Contribution[];
}

export default function RecentContributions({ contributions }: RecentContributionsProps) {
  const navigate = useNavigate();
  const recent = contributions.slice(0, 8);

  return (
    <div style={narrativeSection}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <div style={{ ...sectionTitle, marginBottom: 0, display: 'flex', alignItems: 'center', gap: 4 }}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"/></svg>
          RECENT CONTRIBUTIONS
        </div>
        <span
          onClick={() => navigate('/feed')}
          style={{ ...mono, fontSize: 10, color: 'var(--accent-blue)', cursor: 'pointer' }}
        >
          View full feed →
        </span>
      </div>
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '2fr 2.5fr 1.5fr 5fr 1fr',
            gap: 12,
            padding: '6px 16px',
            borderBottom: '1px solid var(--border-subtle)',
            background: 'var(--bg-surface)',
            fontFamily: 'var(--font-mono)',
            fontSize: 10,
            color: 'var(--text-tertiary)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
          }}
        >
          <div>Date</div>
          <div>MP</div>
          <div>Type</div>
          <div>Subject</div>
          <div style={{ textAlign: 'right' }}>Source</div>
        </div>
        {recent.map((c) => (
          <div
            key={c.id}
            style={{
              display: 'grid',
              gridTemplateColumns: '2fr 2.5fr 1.5fr 5fr 1fr',
              gap: 12,
              padding: '8px 16px',
              alignItems: 'center',
              borderBottom: '1px solid var(--border-subtle)',
              cursor: c.mp_id ? 'pointer' : 'default',
            }}
            onClick={() => {
              if (c.mp_id) navigate(`/mp/${c.mp_id}`);
            }}
          >
            <div style={{ ...mono, fontSize: 11, color: 'var(--text-secondary)' }}>{c.date}</div>
            <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-primary)' }}>
              {c.mp_name || 'Unresolved'}
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
                  onClick={(e) => e.stopPropagation()}
                  style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)', textDecoration: 'none' }}
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

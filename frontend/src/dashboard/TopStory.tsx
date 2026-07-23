import { useState } from 'react';
import { Contribution } from './types';
import { card, sectionTitle, mono, typeTag, avatarMono, initials } from './styles';

interface TopStoryProps {
  contribution: Contribution | null;
}

export default function TopStory({ contribution }: TopStoryProps) {
  const [expanded, setExpanded] = useState(false);

  if (!contribution) {
    return null;
  }

  const mpLabel = contribution.mp_name ?? contribution.constituency ?? 'Unresolved MP';

  return (
    <div style={{ ...card, cursor: 'pointer' }} onClick={() => setExpanded((prev) => !prev)}>
      <div style={sectionTitle}>Top Story</div>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <div style={avatarMono(36)}>{initials(mpLabel)}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span style={typeTag(contribution.contribution_type)}>{contribution.contribution_type}</span>
            <span style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)' }}>{contribution.date}</span>
          </div>
          <div style={{ fontSize: 15, color: 'var(--text-primary)', marginBottom: 8 }}>
            {contribution.subject_text.slice(0, 140)}
            {contribution.subject_text.length > 140 ? '…' : ''}
          </div>
          <div style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)' }}>
            {mpLabel} · {contribution.ministry_addressed || 'No ministry'}
          </div>
        </div>
      </div>

      {expanded && (
        <div
          style={{
            marginTop: 12,
            paddingTop: 12,
            borderTop: '1px solid var(--border-subtle)',
            fontSize: 13,
            color: 'var(--text-secondary)',
          }}
        >
          <p>{contribution.subject_text}</p>
          <a
            href={contribution.source_url}
            target="_blank"
            rel="noreferrer"
            style={{ ...mono, fontSize: 11, color: 'var(--accent-blue)' }}
            onClick={(e) => e.stopPropagation()}
          >
            Read full Q&amp;A →
          </a>
        </div>
      )}
    </div>
  );
}

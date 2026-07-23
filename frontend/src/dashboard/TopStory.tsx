import { Contribution } from './types';
import { narrativeSection, sectionTitle, storyCard, mono, typeTag, avatarMono, initials } from './styles';

interface TopStoryProps {
  contribution: Contribution | null;
}

export default function TopStory({ contribution }: TopStoryProps) {
  if (!contribution) {
    return null;
  }

  const mpLabel = contribution.mp_name ?? contribution.constituency ?? 'Unresolved MP';

  return (
    <div style={narrativeSection}>
      <div style={{ ...sectionTitle, display: 'flex', alignItems: 'center', gap: 4 }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
        TOP STORY THIS WEEK
      </div>
      <div style={storyCard}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
          <div
            style={{
              ...avatarMono(36),
              fontSize: 12,
              borderColor: 'var(--accent-amber)',
            }}
          >
            {initials(mpLabel)}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={typeTag(contribution.contribution_type)}>
                {contribution.contribution_type.toUpperCase()}
              </span>
              <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                {contribution.date}
              </span>
            </div>
            <div
              style={{
                fontSize: 14,
                fontWeight: 600,
                color: 'var(--text-primary)',
                marginBottom: 4,
                lineHeight: 1.3,
              }}
            >
              {contribution.subject_text.slice(0, 140)}
              {contribution.subject_text.length > 140 ? '…' : ''}
            </div>
            <p
              style={{
                fontSize: 12,
                color: 'var(--text-secondary)',
                lineHeight: 1.5,
                margin: 0,
              }}
            >
              {contribution.subject_text}
            </p>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginTop: 8,
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
              }}
            >
              <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>Read full Q&amp;A →</span>
              <span style={{ color: 'var(--text-tertiary)' }}>·</span>
              <span style={{ color: 'var(--text-tertiary)' }}>
                Source: {contribution.source_url ? 'Notice Paper' : 'Unknown'}
              </span>
              <span style={{ color: 'var(--text-tertiary)' }}>·</span>
              <span style={{ color: 'var(--text-tertiary)' }}>
                Ministry: {contribution.ministry_addressed || 'Not specified'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import { Contribution, TopStoryNarrative } from './types';
import { narrativeSection, sectionTitle, storyCard, mono, typeTag, avatarMono, initials } from './styles';

interface TopStoryProps {
  contribution: Contribution | null;
  narrative: TopStoryNarrative | null;
}

export default function TopStory({ contribution, narrative }: TopStoryProps) {
  if (!contribution && !narrative) {
    return null;
  }

  const mpLabel = narrative?.mp_name ?? contribution?.mp_name ?? contribution?.constituency ?? 'Unresolved MP';
  const ministry = narrative?.ministry ?? contribution?.ministry_addressed ?? 'Not specified';
  const ctype = narrative?.contribution_type ?? contribution?.contribution_type ?? '';
  const date = narrative?.date ?? contribution?.date ?? '';
  const isInferred = narrative ? (contribution?.ministry_addressed !== ministry && ministry !== 'Not specified') : false;

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
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={typeTag(ctype)}>
                {ctype.replace(/_/g, ' ').toUpperCase()}
              </span>
              <span style={{ ...mono, fontSize: 10, color: 'var(--text-tertiary)' }}>
                {date}
              </span>
              <span style={{ color: 'var(--text-tertiary)' }}>·</span>
              <span style={{ ...mono, fontSize: 10, color: 'var(--accent-amber)' }}>
                {ministry}{isInferred ? ' (Inferred)' : ''}
              </span>
            </div>

            {narrative ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 9,
                      color: 'var(--accent-blue)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                      marginRight: 8,
                    }}
                  >
                    THE ACTION
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                    {narrative.action}
                  </span>
                </div>
                <div>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 9,
                      color: 'var(--text-tertiary)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                      marginRight: 8,
                    }}
                  >
                    THE CONTEXT
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {narrative.context}
                  </span>
                </div>
                <div>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: 9,
                      color: 'var(--accent-green)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                      marginRight: 8,
                    }}
                  >
                    IMPACT
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--text-primary)', lineHeight: 1.5 }}>
                    {narrative.impact}
                  </span>
                </div>
              </div>
            ) : (
              <>
                <div
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    marginBottom: 4,
                    lineHeight: 1.3,
                  }}
                >
                  {contribution?.subject_text?.slice(0, 140)}
                  {contribution?.subject_text && contribution.subject_text.length > 140 ? '…' : ''}
                </div>
                <p
                  style={{
                    fontSize: 12,
                    color: 'var(--text-secondary)',
                    lineHeight: 1.5,
                    margin: 0,
                  }}
                >
                  {contribution?.subject_text}
                </p>
              </>
            )}

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginTop: 10,
                fontFamily: 'var(--font-mono)',
                fontSize: 10,
              }}
            >
              <span style={{ color: 'var(--accent-blue)', cursor: 'pointer' }}>Read full Q&amp;A →</span>
              <span style={{ color: 'var(--text-tertiary)' }}>·</span>
              <span style={{ color: 'var(--text-tertiary)' }}>
                Source: {contribution?.source_url ? 'Notice Paper' : 'Unknown'}
              </span>
              <span style={{ color: 'var(--text-tertiary)' }}>·</span>
              <span style={{ color: 'var(--text-tertiary)' }}>
                Ministry: {ministry}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

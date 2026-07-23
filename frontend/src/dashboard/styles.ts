import { CSSProperties } from 'react';

export const card: CSSProperties = {
  border: '1px solid var(--border-subtle)',
  background: 'var(--bg-surface)',
  padding: 16,
};

export const sectionTitle: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 11,
  letterSpacing: '0.05em',
  textTransform: 'uppercase',
  color: 'var(--text-tertiary)',
  marginBottom: 10,
};

export const mono: CSSProperties = {
  fontFamily: 'var(--font-mono)',
};

export const statValue: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 28,
  color: 'var(--text-primary)',
  lineHeight: 1.1,
};

export const statLabel: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 11,
  color: 'var(--text-tertiary)',
  marginTop: 4,
};

export const grid: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(4, 1fr)',
  gap: 12,
};

const TAG_COLORS: Record<string, string> = {
  question: 'var(--accent-blue)',
  oral_question: 'var(--accent-blue)',
  motion: 'var(--accent-amber)',
  tabling: 'var(--accent-green)',
  bill_presentation: 'var(--accent-green)',
  amendment: 'var(--accent-red)',
};

export function typeTag(contributionType: string): CSSProperties {
  const color = TAG_COLORS[contributionType] ?? 'var(--text-secondary)';
  return {
    fontFamily: 'var(--font-mono)',
    fontSize: 9,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    padding: '2px 6px',
    color,
    border: `1px solid ${color}`,
    background: 'transparent',
    display: 'inline-block',
  };
}

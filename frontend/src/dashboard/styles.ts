import { CSSProperties } from 'react';

export const narrativeSection: CSSProperties = {
  marginBottom: 20,
};

export const sectionTitle: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 11,
  letterSpacing: '0.08em',
  textTransform: 'uppercase',
  color: 'var(--text-tertiary)',
  marginBottom: 10,
};

export const mono: CSSProperties = {
  fontFamily: 'var(--font-mono)',
};

export const statCard: CSSProperties = {
  border: '1px solid var(--border-subtle)',
  background: 'var(--bg-elevated)',
  padding: 12,
};

export const statValue: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 20,
  fontWeight: 600,
  color: 'var(--text-primary)',
  lineHeight: 1.1,
  marginTop: 2,
};

export const statLabel: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  letterSpacing: '0.05em',
  textTransform: 'uppercase',
  color: 'var(--text-tertiary)',
};

export const grid4: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(4, 1fr)',
  gap: 12,
};

export const grid2: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: 16,
};

export const surface: CSSProperties = {
  background: 'var(--bg-surface)',
  border: '1px solid var(--border-subtle)',
};

export const surfaceElevated: CSSProperties = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border-default)',
};

export const storyCard: CSSProperties = {
  borderLeft: '3px solid var(--accent-blue)',
  borderTop: '1px solid var(--border-subtle)',
  borderRight: '1px solid var(--border-subtle)',
  borderBottom: '1px solid var(--border-subtle)',
  padding: 12,
  background: 'var(--bg-elevated)',
  cursor: 'pointer',
};

export const barThin: CSSProperties = {
  height: 2,
  background: 'var(--bg-elevated)',
};

export const statusDot: CSSProperties = {
  width: 6,
  height: 6,
  display: 'inline-block',
};

export function avatarMono(size = 28): CSSProperties {
  return {
    width: size,
    height: size,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: 'var(--font-mono)',
    fontSize: size <= 28 ? 10 : 12,
    fontWeight: 600,
    border: '1px solid var(--border-default)',
    background: 'var(--bg-elevated)',
    color: 'var(--text-primary)',
    flexShrink: 0,
  };
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? '';
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : '';
  return (first + last).toUpperCase();
}

export const TAG_ORAL_Q = 'var(--accent-blue)';
export const TAG_AMBER = 'var(--accent-amber)';
export const TAG_GREEN = 'var(--accent-green)';
export const TAG_RED = 'var(--accent-red)';

const TAG_COLORS: Record<string, string> = {
  question: TAG_ORAL_Q,
  oral_question: TAG_ORAL_Q,
  oral_q: TAG_ORAL_Q,
  minist_q: TAG_RED,
  motion: TAG_AMBER,
  tabling: TAG_GREEN,
  bill_presentation: TAG_GREEN,
  bill_1st: TAG_GREEN,
  bill_2nd: TAG_GREEN,
  bill_3rd: TAG_GREEN,
  amendment: TAG_RED,
};

const TYPE_LABELS: Record<string, string> = {
  question: 'Question',
  oral_question: 'Question',
  oral_q: 'Question',
  minist_question: "Minister's Q&A",
  minist_q: "Minister's Q&A",
  motion: 'Motion',
  bill_presentation: 'New Bill',
  bill_1st: 'Bill: Introduced',
  bill_2nd: 'Bill: Debated',
  bill_3rd: 'Bill: Final Vote',
  bill_reading: 'Bill: Reading',
  bill_amendment: 'Bill Change',
  committee_of_supply: 'Budget Review',
  tabling: 'Document Filed',
  amendment: 'Bill Change',
  petition: 'Petition',
  ministerial_statement: "Minister's Update",
  question_without_notice: 'Question',
};

export function typeLabel(contributionType: string): string {
  return TYPE_LABELS[contributionType.toLowerCase()]
    ?? contributionType.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function typeTag(contributionType: string): CSSProperties {
  const color = TAG_COLORS[contributionType.toLowerCase()] ?? 'var(--text-secondary)';
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

export const ACCENT_ROTATION = [TAG_AMBER, TAG_ORAL_Q, TAG_GREEN] as const;

export const pillLink: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  color: 'var(--accent-blue)',
  textDecoration: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  gap: 4,
  cursor: 'pointer',
};

export const statRow: CSSProperties = {
  display: 'flex',
  alignItems: 'baseline',
  justifyContent: 'space-between',
  padding: '6px 0',
  borderBottom: '1px solid var(--border-subtle)',
};

export const statRowLast: CSSProperties = {
  ...statRow,
  borderBottom: 'none',
};

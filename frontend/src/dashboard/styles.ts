import { CSSProperties } from 'react';

export const card: CSSProperties = {
  border: '1px solid var(--border-subtle)',
  background: 'var(--bg-surface)',
  padding: 16,
};

export const statCard: CSSProperties = {
  border: '1px solid var(--border-subtle)',
  background: 'var(--bg-elevated)',
  padding: 12,
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

export const surfaceElevated: CSSProperties = {
  background: 'var(--bg-elevated)',
  border: '1px solid var(--border-default)',
};

export function avatarMono(size = 28): CSSProperties {
  return {
    ...surfaceElevated,
    width: size,
    height: size,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: 'var(--font-mono)',
    fontSize: size <= 28 ? 10 : 12,
    fontWeight: 600,
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

export const ACCENT_ROTATION = ['var(--accent-amber)', 'var(--accent-blue)', 'var(--accent-green)'];

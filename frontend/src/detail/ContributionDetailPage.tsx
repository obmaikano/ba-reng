import { useEffect, useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { get } from '../api';
import { Contribution } from '../dashboard/types';
import { typeLabel } from '../dashboard/styles';

/* ── Inline text structure parser ────────────────────────────────── */

interface TextBlock {
  kind: 'intro' | 'roman-item' | 'alpha-item' | 'numbered-item' | 'paragraph' | 'heading';
  text: string;
  marker?: string;
}

// Split on patterns like "; (i)", ": (i)", ", (i)" or standalone "(i)" at sentence breaks.
// The intro is everything before the first sub-item marker.
// Not used — see splitByRoman below
// Not used — see splitByAlpha below
const ROMAN_EXTRACT = /^\s*\(([ivx]+)\)\s+/i;
const ALPHA_EXTRACT = /^\s*\(([a-z])\)\s+/i;
// Valid separators before roman/alpha markers
const SEP = '[;:,\u2013\u2014\u002D]';  // ; : , en-dash em-dash hyphen
function isOnlySep(s: string): boolean {
  return /^[;:,\u2013\u2014\u002D\s]+$/.test(s);
}


function splitByRoman(raw: string): string[] {
  // Split on (i), (ii), (iii)... when preceded by a separator + optional space
  // and NOT preceded by ) (avoids nested markers like (b)(i))
  const first = raw.search(new RegExp('(?:^|' + SEP + ')\\s*(?=\\([ivx]+\\))', 'i'));
  if (first < 0) return [raw];

  const intro = raw.slice(0, first).replace(new RegExp('[' + SEP + ']\\s*$', 'g'), '').trim();
  const remainder = raw.slice(first);
  const parts = remainder
    .split(new RegExp('\\s*(?=\\([ivx]+\\)\\s)', 'i'))
    .filter((s: string) => s.trim())
    .filter((s: string) => !isOnlySep(s));

  return [intro, ...parts];
}

function splitByAlpha(raw: string): string[] {
  // Split on (a), (b), (c)... when preceded by a separator — but NOT when
  // preceded by ) or a word character (avoids nested like (b)(i) or entry (e))
  const first = raw.search(new RegExp('(?:^|' + SEP + ')\\s*(?=\\([a-z]\\)\\s)', 'i'));
  if (first < 0) return [raw];

  const intro = raw.slice(0, first).replace(new RegExp('[' + SEP + ']\\s*$', 'g'), '').trim();
  const remainder = raw.slice(first);
  // Only split if the alpha marker is followed by whitespace and then a word
  const parts = remainder
    .split(new RegExp('\\s*(?=\\([a-z]\\)\\s)', 'i'))
    .filter((s: string) => s.trim())
    .filter((s: string) => !isOnlySep(s));

  return [intro, ...parts];
}

function parseStructuredText(raw: string): TextBlock[] {
  if (!raw || !raw.trim()) return [];

  // First, try to split on roman numeral sub-items: (i), (ii), (iii)...
  const romanParts = splitByRoman(raw);
  if (romanParts.length > 1) {
    const blocks: TextBlock[] = [];
    const intro = romanParts[0].trim();
    if (intro) blocks.push({ kind: 'intro', text: intro });

    for (const part of romanParts.slice(1)) {
      const m = ROMAN_EXTRACT.exec(part);
      if (m) {
        blocks.push({
          kind: 'roman-item',
          text: part.slice(m[0].length).trim(),
          marker: m[1].toUpperCase(),
        });
      } else {
        // fallback: treat as paragraph
        if (part.trim()) blocks.push({ kind: 'paragraph', text: part.trim() });
      }
    }
    return blocks;
  }

  // Second, try alpha sub-items: (a), (b), (c)...
  const alphaParts = splitByAlpha(raw);
  if (alphaParts.length > 1) {
    const blocks: TextBlock[] = [];
    const intro = alphaParts[0].trim();
    if (intro) blocks.push({ kind: 'intro', text: intro });

    for (const part of alphaParts.slice(1)) {
      const m = ALPHA_EXTRACT.exec(part.trim());
      if (m) {
        blocks.push({
          kind: 'alpha-item',
          text: part.trim().slice(m[0].length).trim(),
          marker: m[1],
        });
      } else if (part.trim()) {
        blocks.push({ kind: 'paragraph', text: part.trim() });
      }
    }
    return blocks;
  }

  // Fallback: plain paragraphs by double-newline
  const paragraphs = raw.split(/\n{2,}/).filter((p) => p.trim());
  return paragraphs.map((p) => ({ kind: 'paragraph', text: p.trim() }));
}

/* ── Structured text card ───────────────────────────────────────── */

function StructuredTextCard({ subject, isBill }: { subject: string; isBill?: boolean }) {
  const blocks = useMemo(() => parseStructuredText(subject), [subject]);
  const hasStructured = blocks.some(
    (b) => b.kind === 'roman-item' || b.kind === 'alpha-item' || b.kind === 'numbered-item',
  );
  const borderColor = isBill ? 'var(--accent-green)' : 'var(--accent-blue)';

  // Plain text: use pre-line for natural line preservation
  if (!hasStructured) {
    return (
      <div style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderLeft: `3px solid ${borderColor}`,
        padding: '18px 20px',
      }}>
        <p style={{
          fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.9,
          margin: 0, whiteSpace: 'pre-line', wordBreak: 'break-word',
        }}>
          {subject}
        </p>
      </div>
    );
  }

  // Structured text: intro + item list
  const intro = blocks.find((b) => b.kind === 'intro');
  const items = blocks.filter((b) => b.kind !== 'intro');

  return (
    <div style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-subtle)',
      padding: 0,
    }}>
      {/* Intro */}
      {intro && (
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
        }}>
          <p style={{
            fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.9,
            margin: 0, whiteSpace: 'pre-line', wordBreak: 'break-word',
          }}>
            {intro.text}
          </p>
        </div>
      )}

      {/* Items */}
      <div style={{ padding: '8px 20px 12px 20px' }}>
        {items.map((block, i) => {
          if (block.kind === 'paragraph') {
            return (
              <p
                key={i}
                style={{
                  fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.9,
                  margin: i === 0 ? '4px 0 0 0' : '12px 0 0 0',
                  whiteSpace: 'pre-line', wordBreak: 'break-word',
                }}
              >
                {block.text}
              </p>
            );
          }

          const markerColor =
            block.kind === 'alpha-item' ? 'var(--accent-amber)' : 'var(--accent-blue)';
          const markerLabel =
            block.kind === 'roman-item'
              ? `(\${block.marker!.toLowerCase()})`
              : block.kind === 'alpha-item'
                ? `(\${block.marker})`
                : `\${block.marker}.`;

          return (
            <div
              key={i}
              style={{
                display: 'flex',
                gap: 12,
                padding: '10px 0',
                borderBottom:
                  i < items.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                alignItems: 'flex-start',
              }}
            >
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: 10,
                  fontWeight: 600,
                  color: markerColor,
                  minWidth: 28,
                  flexShrink: 0,
                  textTransform: 'uppercase' as const,
                  paddingTop: 1,
                }}
              >
                {markerLabel}
              </span>
              <span style={{
                fontSize: 13, color: 'var(--text-primary)',
                lineHeight: 1.8, flex: 1, wordBreak: 'break-word',
                whiteSpace: 'pre-line',
              }}>
                {block.text}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Meta field ─────────────────────────────────────────────────── */

function MetaField({
  label,
  value,
  isLink,
  onClick,
}: {
  label: string;
  value: string;
  isLink?: boolean;
  onClick?: () => void;
}) {
  return (
    <div style={{ background: 'var(--bg-elevated)', padding: '12px 14px' }}>
      <span
        style={{
          fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)',
          textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block',
        }}
      >
        {label}
      </span>
      <span
        onClick={onClick}
        style={{
          display: 'block', marginTop: 4, fontSize: 12, fontWeight: 500,
          color: isLink ? 'var(--accent-blue)' : 'var(--text-primary)',
          cursor: isLink ? 'pointer' : 'default',
          lineHeight: 1.4,
        }}
      >
        {value}
      </span>
    </div>
  );
}

/* ── Main page component ────────────────────────────────────────── */

export default function ContributionDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [contribution, setContribution] = useState<Contribution | null>(null);
  const [related, setRelated] = useState<Contribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    get<Contribution>(`/api/v1/contributions/${id}`)
      .then((c) => {
        setContribution(c);
        setError(null);
        const params: string[] = ['limit=10'];
        if (c.ministry_addressed)
          params.push(`ministry=${encodeURIComponent(c.ministry_addressed)}`);
        return get<{ data: Contribution[] }>(
          `/api/v1/contributions?${params.join('&')}`,
        );
      })
      .then((resp) => {
        if (resp?.data) {
          setRelated(resp.data.filter((r) => r.id !== Number(id)).slice(0, 8));
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load contribution');
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--text-tertiary)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          Loading contribution…
        </span>
      </div>
    );
  }

  if (error || !contribution) {
    return (
      <div style={{ padding: 24 }}>
        <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          {error || 'Contribution not found.'}
        </span>
        <div style={{ marginTop: 12 }}>
          <span onClick={() => navigate('/feed')} style={{ color: 'var(--accent-blue)', cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            ← Back to feed
          </span>
        </div>
      </div>
    );
  }

  const dateStr = new Date(contribution.date).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  });
  const cType = contribution.contribution_type;
  const isBill = cType.startsWith('bill_');

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 9, textTransform: 'uppercase', letterSpacing: '0.05em',
            padding: '3px 8px', color: isBill ? 'var(--accent-green)' : 'var(--accent-blue)',
            border: `1px solid ${isBill ? 'var(--accent-green)' : 'var(--accent-blue)'}`,
            background: isBill ? 'rgba(22,163,74,0.1)' : 'rgba(45,127,249,0.1)',
          }}>
            {typeLabel(cType)}
          </span>
        </div>
        <h1 style={{
          fontSize: 18, fontWeight: 600, color: 'var(--text-primary)',
          margin: '0 0 4px 0', lineHeight: 1.4,
        }}>
          {(contribution.subject_text || '').split(/[.;]\s/)[0].trim().slice(0, 160)
            || contribution.subject_text.slice(0, 160)}
        </h1>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)' }}>
          {dateStr}
        </span>
      </div>

      {/* Metadata grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr',
        gap: 1, marginBottom: 24,
        background: 'var(--border-subtle)',
      }}>
        <MetaField label="Date" value={dateStr} />
        <MetaField label="Type" value={typeLabel(cType)} />
        <MetaField
          label="Ministry"
          value={contribution.ministry_addressed || '—'}
          isLink={!!contribution.ministry_addressed}
          onClick={() => {
            if (contribution.ministry_addressed) navigate(`/ministry/${encodeURIComponent(contribution.ministry_addressed)}`);
          }}
        />
        <MetaField
          label="Member of Parliament"
          value={contribution.mp_name || contribution.raw_match_name || '—'}
          isLink={!!contribution.mp_id}
          onClick={() => {
            if (contribution.mp_id) navigate(`/mp/${contribution.mp_id}`);
          }}
        />
        <MetaField label="Party" value={contribution.party || '—'} />
        <MetaField
          label="Constituency"
          value={contribution.constituency || '—'}
          isLink={!!contribution.constituency}
          onClick={() => {
            if (contribution.constituency) navigate(`/constituency/${encodeURIComponent(contribution.constituency)}`);
          }}
        />
      </div>

      {/* Full text */}
      <div style={{ marginBottom: 24 }}>
        <span style={{
          fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)',
          textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 10,
        }}>
          Full Text
        </span>
        <StructuredTextCard subject={contribution.subject_text} isBill={isBill} />
      </div>

      {/* Source document */}
      {(contribution.doc_source_url || contribution.source_url) && (
        <div style={{
          marginBottom: 24, padding: 14,
          background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)',
          borderLeft: '3px solid var(--accent-blue)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
            </svg>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Source Document
            </span>
          </div>
          <a
            href={contribution.doc_source_url || contribution.source_url}
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'block', marginTop: 6, fontFamily: 'var(--font-mono)', fontSize: 11,
              color: 'var(--accent-blue)', textDecoration: 'none', wordBreak: 'break-all',
            }}
          >
            {contribution.doc_source_url || contribution.source_url}
          </a>
        </div>
      )}

      {/* Related */}
      {related.length > 0 && (
        <div>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)',
            textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: 10,
          }}>
            Related
            {contribution.ministry_addressed && (
              <span style={{ marginLeft: 6, color: 'var(--text-tertiary)' }}>
                · {contribution.ministry_addressed}
              </span>
            )}
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {related.map((r) => (
              <div
                key={r.id}
                onClick={() => navigate(`/contribution/${r.id}`)}
                style={{
                  background: 'var(--bg-elevated)', border: '1px solid var(--border-default)',
                  padding: 10, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
                }}
              >
                <span style={{
                  fontFamily: 'var(--font-mono)', fontSize: 9, textTransform: 'uppercase',
                  padding: '2px 6px', border: '1px solid var(--border-subtle)',
                  color: 'var(--text-secondary)', flexShrink: 0,
                }}>
                  {typeLabel(r.contribution_type)}
                </span>
                <span style={{
                  fontSize: 11, color: 'var(--text-secondary)', flex: 1,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {r.subject_text.slice(0, 120)}{r.subject_text.length > 120 ? '…' : ''}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-tertiary)' }}>
                  {new Date(r.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

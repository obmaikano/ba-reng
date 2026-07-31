import { ReactNode } from 'react';

export default function AboutPage() {
  return (
    <div style={{ padding: 24, maxWidth: 720 }}>
      <h1 style={{ fontSize: 20, fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 4px 0' }}>
        About Ba Reng?
      </h1>
      <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)', margin: '0 0 24px 0' }}>
        Ba Reng? — "What are they saying?" in Setswana — monitors Botswana Parliament activity through publicly available documents.
      </p>

      <Section title="Data Sources">
        <p>All data is extracted from documents published on <a href="https://www.parliament.gov.bw" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-blue)' }}>parliament.gov.bw</a> and <a href="https://botswanaspeaks.org" target="_blank" rel="noreferrer" style={{ color: 'var(--accent-blue)' }}>botswanaspeaks.org</a>:</p>
        <ul>
          <li><strong>Order Papers</strong> — daily agenda listing oral questions, motions, and bill stages</li>
          <li><strong>Notice Papers</strong> — advance notice of questions to be asked</li>
          <li><strong>Hansard transcripts</strong> — verbatim debate records with speaker attribution</li>
          <li><strong>Committee of Supply speeches</strong> — budget debate contributions</li>
          <li><strong>Ministerial Statements</strong> — policy updates delivered by ministers</li>
        </ul>
      </Section>

      <Section title="Participation Index">
        <p>The Participation Index is a weighted score that measures an MP's recorded activity. Different contribution types carry different weights reflecting the effort and impact of each intervention:</p>
        <ul>
          <li><strong>Oral Questions</strong> — weight 1.0 (direct accountability mechanism)</li>
          <li><strong>Motions</strong> — weight 1.5 (substantive legislative proposals)</li>
          <li><strong>Bill presentations and readings</strong> — weight 2.0 (legislative sponsorship)</li>
          <li><strong>Committee of Supply interventions</strong> — weight 1.2 (budget oversight)</li>
          <li><strong>Ministerial Statements</strong> — weight 0.8 (ministerial duty, not discretionary)</li>
        </ul>
        <CaveatCallout>
          The Participation Index is a <strong>proxy metric</strong>. It measures recorded contributions only, not attendance, voting behaviour, committee work, constituency service, or behind-the-scenes legislative activity. Botswana Parliament does not publish attendance or voting records.
        </CaveatCallout>
      </Section>

      <Section title="Executive Responsiveness Scorecard">
        <p>Measures how promptly ministers answer parliamentary questions. Two sub-metrics:</p>
        <ul>
          <li><strong>Deferral Rate</strong> — percentage of questions deferred to "a Later Date" rather than answered directly</li>
          <li><strong>Average Answer Lag</strong> — mean days between question submission and ministerial response</li>
        </ul>
        <p>Grades: <span style={{ color: 'var(--accent-green)', fontWeight: 600 }}>A</span> (&lt;10% deferral, &lt;14 days), <span style={{ color: 'var(--accent-amber)', fontWeight: 600 }}>C</span> (moderate), <span style={{ color: 'var(--accent-red)', fontWeight: 600 }}>F</span> (&gt;30% deferral or &gt;30 days).</p>
      </Section>

      <Section title="CLAI — Constituency Local Alignment Index">
        <p>Measures how often an MP's contributions reference their own constituency. Cross-references speech text against the official Botswana gazetteer of settlements, wards, and local landmarks.</p>
        <p>Score = (local mentions &divide; total contributions) &times; 100. A higher CLAI score indicates stronger grounding in constituency-specific issues.</p>
      </Section>

      <Section title="Evidence Classification (Debate)">
        <p>Hansard debate utterances are classified into four evidence types:</p>
        <ul>
          <li><strong>Empirical</strong> — cites data, statistics, reports, or measurable facts</li>
          <li><strong>Statutory</strong> — references legislation, Standing Orders, or constitutional provisions</li>
          <li><strong>Anecdotal</strong> — relies on personal experience, constituency stories, or illustrative examples</li>
          <li><strong>Normative</strong> — argues from principle, values, or what "should" be done</li>
        </ul>
      </Section>

      <Section title="Limitations">
        <ul>
          <li>Data coverage depends on document availability. Not all parliamentary sittings produce publicly accessible PDFs.</li>
          <li>MP-to-contribution resolution uses name matching with fallback heuristics. Unmatched names are queued for manual review.</li>
          <li>Setswana-language content in Hansard is detected via language tagging; translations rely on the parliamentary glossary.</li>
          <li>This is a monitoring tool, not an official parliamentary record. Always verify against primary sources.</li>
        </ul>
      </Section>

      <div style={{ marginTop: 32, padding: 16, background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', textAlign: 'center' }}>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '0 0 4px 0' }}>
          Built with public data. Not affiliated with the Parliament of Botswana.
        </p>
        <p style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', margin: 0 }}>
          ba-reng v1.0 &middot; {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ marginBottom: 24 }}>
      <h2 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 8px 0', paddingBottom: 6, borderBottom: '1px solid var(--border-subtle)' }}>
        {title}
      </h2>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7 }}>
        {children}
      </div>
    </div>
  );
}

function CaveatCallout({ children }: { children: ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, padding: 10, marginTop: 10, background: 'rgba(245,166,35,0.08)', border: '1px solid rgba(245,166,35,0.2)' }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--accent-amber)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 1, flexShrink: 0 }}>
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
      </svg>
      <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>{children}</p>
    </div>
  );
}

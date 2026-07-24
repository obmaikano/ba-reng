import { narrativeSection } from './styles';

export default function CaveatBanner() {
  return (
    <div style={narrativeSection}>
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 10,
          padding: 12,
          background: 'var(--bg-surface)',
          borderLeft: '3px solid var(--accent-amber)',
        }}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--accent-amber)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ marginTop: 2, flexShrink: 0 }}
        >
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <div>
          <h4
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: 'var(--accent-amber)',
              margin: 0,
              marginBottom: 4,
            }}
          >
            Constraint: No Attendance Data
          </h4>
          <p
            style={{
              fontSize: 11,
              color: 'var(--text-secondary)',
              margin: 0,
              lineHeight: 1.5,
            }}
          >
            This narrative reflects{' '}
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-primary)',
              }}
            >
              RECORDED_CONTRIBUTIONS
            </span>{' '}
            only. Botswana Parliament does not publish attendance records. A low count does not mean
            absence — MPs engage in committee work, constituency duties, and silent voting.
          </p>
          <a
            href="#"
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10,
              color: 'var(--accent-blue)',
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              marginTop: 4,
            }}
          >
            VIEW_METHODOLOGY →
          </a>
        </div>
      </div>
    </div>
  );
}

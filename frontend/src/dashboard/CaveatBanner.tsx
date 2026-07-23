interface CaveatBannerProps {
  caveat: string;
}

export default function CaveatBanner({ caveat }: CaveatBannerProps) {
  return (
    <div
      style={{
        display: 'flex',
        gap: 10,
        padding: 12,
        background: 'var(--bg-surface)',
        borderLeft: '3px solid var(--accent-amber)',
      }}
    >
      <span style={{ color: 'var(--accent-amber)', fontSize: 14 }}>!</span>
      <div>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--accent-amber)',
            marginBottom: 4,
          }}
        >
          Constraint: No Attendance Data
        </div>
        <p style={{ fontSize: 11, color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
          {caveat} Botswana Parliament does not publish attendance records — a low count
          does not mean absence.
        </p>
      </div>
    </div>
  );
}

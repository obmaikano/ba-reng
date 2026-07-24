export interface FilterState {
  type: string;
  party: string;
  ministry: string;
  constituency: string;
  startDate: string;
  endDate: string;
}

export const DEFAULT_FILTERS: FilterState = {
  type: 'All Types',
  party: 'All Parties',
  ministry: 'All Ministries',
  constituency: '',
  startDate: '',
  endDate: '',
};

interface FilterSidebarProps {
  ministries: string[];
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  ministryCounts?: Record<string, number>;
}

export default function FilterSidebar({ ministries, filters, onChange, ministryCounts }: FilterSidebarProps) {
  const set = (key: keyof FilterState, value: string) => {
    onChange({ ...filters, [key]: value });
  };

  const reset = () => onChange({ ...DEFAULT_FILTERS });

  const sidebarLabel: React.CSSProperties = {
    fontFamily: 'var(--font-mono)',
    fontSize: 10,
    color: 'var(--text-tertiary)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    display: 'block',
    marginBottom: 4,
  };

  const selectStyle: React.CSSProperties = {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border-default)',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    padding: '5px 8px',
    width: '100%',
    outline: 'none',
    cursor: 'pointer',
    WebkitAppearance: 'none',
    appearance: 'none',
    backgroundImage: `url("data:image/svg+xml,%3Csvg width='10' height='6' viewBox='0 0 10 6' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M1 1L5 5L9 1' stroke='%238B95A4' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 8px center',
    paddingRight: 24,
  };

  const inputStyle: React.CSSProperties = {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border-default)',
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-mono)',
    fontSize: 10,
    padding: '5px 8px',
    width: '100%',
    outline: 'none',
    boxSizing: 'border-box',
  };

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Filters</span>
        <span onClick={reset} style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--accent-blue)', cursor: 'pointer' }}>Reset</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div>
          <span style={sidebarLabel}>Type</span>
          <select value={filters.type} onChange={(e) => set('type', e.target.value)} style={selectStyle}>
            <option>All Types</option>
            <option>oral_question</option>
            <option>motion</option>
            <option>bill_presentation</option>
            <option>bill_2nd</option>
            <option>committee_of_supply</option>
            <option>petition</option>
          </select>
        </div>

        <div>
          <span style={sidebarLabel}>Party</span>
          <select value={filters.party} onChange={(e) => set('party', e.target.value)} style={selectStyle}>
            <option>All Parties</option>
            <option>BDP</option>
            <option>UDC</option>
            <option>BCP</option>
            <option>AP</option>
          </select>
        </div>

        <div>
          <span style={sidebarLabel}>Ministry</span>
          <select value={filters.ministry} onChange={(e) => set('ministry', e.target.value)} style={selectStyle}>
            <option>All Ministries</option>
            {ministries.map((m) => (
              <option key={m}>{m}</option>
            ))}
          </select>
        </div>

        <div>
          <span style={sidebarLabel}>Date Range</span>
          <div style={{ display: 'flex', gap: 6 }}>
            <input
              type="text"
              placeholder="2026-01-01"
              value={filters.startDate}
              onChange={(e) => set('startDate', e.target.value)}
              style={{ ...inputStyle, boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.3)' }}
            />
            <input
              type="text"
              placeholder="2026-07-22"
              value={filters.endDate}
              onChange={(e) => set('endDate', e.target.value)}
              style={{ ...inputStyle, boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.3)' }}
            />
          </div>
        </div>

        <div>
          <span style={sidebarLabel}>Constituency</span>
          <input
            type="text"
            placeholder="Search..."
            value={filters.constituency}
            onChange={(e) => set('constituency', e.target.value)}
            style={{ ...inputStyle, boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.3)' }}
          />
        </div>
      </div>

      <div style={{ borderTop: '1px solid var(--border-subtle)', marginTop: 16, paddingTop: 16 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Top Ministries</span>
        <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {ministries.slice(0, 5).map((m) => (
            <div key={m} style={{ display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
              <span style={{ color: 'var(--text-secondary)' }}>{m}</span>
              <span style={{ color: 'var(--accent-blue)' }}>{ministryCounts?.[m] ?? 0}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

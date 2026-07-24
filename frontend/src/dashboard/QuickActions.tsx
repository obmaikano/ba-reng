import { useNavigate } from 'react-router-dom';
import { sectionTitle } from './styles';

export default function QuickActions() {
  const navigate = useNavigate();

  const btnPrimary: React.CSSProperties = {
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    fontWeight: 500,
    background: 'var(--accent-blue)',
    color: 'white',
    padding: '5px 14px',
    border: 'none',
    cursor: 'pointer',
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 5,
  };

  const btnGhost: React.CSSProperties = {
    fontFamily: 'var(--font-mono)',
    fontSize: 11,
    color: 'var(--text-secondary)',
    padding: '4px 10px',
    border: '1px solid var(--border-subtle)',
    background: 'transparent',
    cursor: 'pointer',
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  };

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={sectionTitle}>Quick Actions</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <button style={btnPrimary} onClick={() => navigate('/find')}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          Find Your MP
        </button>
        <button style={btnGhost} onClick={() => navigate('/compare')}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          Compare MPs
        </button>
        <button style={btnGhost} onClick={() => navigate('/bills')}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          Browse Bills
        </button>
      </div>
    </div>
  );
}

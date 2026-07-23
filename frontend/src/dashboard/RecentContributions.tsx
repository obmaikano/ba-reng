import { useNavigate } from 'react-router-dom';
import { Contribution } from './types';
import { card, sectionTitle, mono, typeTag } from './styles';

interface RecentContributionsProps {
  contributions: Contribution[];
}

const columnStyle = { padding: '8px 4px', fontSize: 12 } as const;

export default function RecentContributions({ contributions }: RecentContributionsProps) {
  const navigate = useNavigate();
  const recent = contributions.slice(0, 8);

  return (
    <div style={{ ...card, maxHeight: 340, overflow: 'auto' }}>
      <div style={sectionTitle}>Recent Contributions</div>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-subtle)' }}>
            {['Date', 'MP', 'Type', 'Subject', 'Source'].map((heading) => (
              <th
                key={heading}
                style={{
                  ...mono,
                  fontSize: 10,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  color: 'var(--text-tertiary)',
                  textAlign: 'left',
                  padding: '0 4px 6px',
                }}
              >
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {recent.map((c) => (
            <tr key={c.id} style={{ borderBottom: '1px solid var(--border-subtle)' }}>
              <td style={{ ...columnStyle, ...mono, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
                {c.date}
              </td>
              <td style={columnStyle}>
                {c.mp_id ? (
                  <span
                    onClick={() => navigate(`/mp/${c.mp_id}`)}
                    style={{ cursor: 'pointer', color: 'var(--accent-blue)', fontWeight: 500 }}
                  >
                    {c.mp_name}
                  </span>
                ) : (
                  <span style={{ color: 'var(--text-tertiary)' }}>{c.mp_name ?? 'Unresolved'}</span>
                )}
              </td>
              <td style={columnStyle}>
                <span style={typeTag(c.contribution_type)}>{c.contribution_type}</span>
              </td>
              <td style={{ ...columnStyle, color: 'var(--text-secondary)', maxWidth: 280 }}>
                <span
                  style={{
                    display: 'block',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {c.subject_text}
                </span>
              </td>
              <td style={{ ...columnStyle, textAlign: 'right' }}>
                <a
                  href={c.source_url}
                  target="_blank"
                  rel="noreferrer"
                  style={{ ...mono, fontSize: 11, color: 'var(--text-tertiary)' }}
                >
                  ↗
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

import { StatusData } from './useDashboardData';
import { sectionTitle, mono } from './styles';

interface SystemHealthPanelProps {
  status: StatusData;
}

export default function SystemHealthPanel({ status }: SystemHealthPanelProps) {
  const rows: [string, string, string][] = [
    ['Documents parsed', String(status.document_count), 'var(--accent-blue)'],
    [
      'Unresolved entities',
      String(status.unresolved_entity_count),
      status.unresolved_entity_count > 0 ? 'var(--accent-amber)' : 'var(--accent-green)',
    ],
    ['Last crawl status', status.last_crawl?.status ?? 'UNKNOWN', 'var(--accent-green)'],
  ];

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={sectionTitle}>System Health</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {rows.map(([label, value, color]) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
            <span style={{ color: 'var(--text-secondary)' }}>{label}</span>
            <span style={{ ...mono, color }}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

import { DashboardData } from './useDashboardData';
import QuickActions from './QuickActions';
import ParticipationIndexPreview from './ParticipationIndexPreview';
import SystemHealthPanel from './SystemHealthPanel';
import DataIntegrityNote from './DataIntegrityNote';

interface DashboardSidebarProps {
  data: DashboardData;
}

export default function DashboardSidebar({ data }: DashboardSidebarProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <QuickActions />
      <ParticipationIndexPreview mps={data.mps} />
      <SystemHealthPanel status={data.status} />
      <DataIntegrityNote contributions={data.contributions} />
    </div>
  );
}

import { DashboardData } from './useDashboardData';
import QuickActions from './QuickActions';
import ParticipationIndexPreview from './ParticipationIndexPreview';
import SystemHealthPanel from './SystemHealthPanel';

interface DashboardSidebarProps {
  data: DashboardData;
}

export default function DashboardSidebar({ data }: DashboardSidebarProps) {
  return (
    <div style={{ padding: 4 }}>
      <QuickActions />
      <ParticipationIndexPreview mps={data.mps} />
      <SystemHealthPanel status={data.status} />
    </div>
  );
}

import { useNavigate } from 'react-router-dom';
import { Button } from '@blueprintjs/core';
import { sectionTitle } from './styles';

export default function QuickActions() {
  const navigate = useNavigate();

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={sectionTitle}>Quick Actions</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <Button fill intent="primary" alignText="center" text="Find Your MP" onClick={() => navigate('/find')} />
        <Button fill outlined alignText="center" text="Compare MPs" onClick={() => navigate('/compare')} />
        <Button fill outlined alignText="center" text="Browse Bills" onClick={() => navigate('/bills')} />
      </div>
    </div>
  );
}

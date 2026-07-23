import { useNavigate } from 'react-router-dom';
import { Button } from '@blueprintjs/core';
import { sectionTitle } from './styles';

export default function QuickActions() {
  const navigate = useNavigate();

  return (
    <div style={{ marginBottom: 20 }}>
      <div style={sectionTitle}>Quick Actions</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        <Button fill alignText="left" text="Find My MP" onClick={() => navigate('/find')} />
        <Button fill alignText="left" text="Compare MPs" onClick={() => navigate('/compare')} />
        <Button fill alignText="left" text="Browse Bills" onClick={() => navigate('/bills')} />
      </div>
    </div>
  );
}

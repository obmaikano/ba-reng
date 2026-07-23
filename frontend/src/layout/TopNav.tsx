import { useNavigate } from 'react-router-dom';
import { Button } from '@blueprintjs/core';
import { useAuth } from '../auth/AuthContext';

export default function TopNav() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  return (
    <nav
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: 40,
        padding: '0 12px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'var(--bg-surface)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 14,
            color: 'var(--text-primary)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
          onClick={() => navigate('/')}
        >
          Ba Reng?
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
          v0.1.0
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <Button
          minimal
          small
          text="Week"
          onClick={() => navigate('/')}
        />
        <Button
          minimal
          small
          text="Feed"
          onClick={() => navigate('/feed')}
        />
        <Button
          minimal
          small
          text="Find MP"
          onClick={() => navigate('/find')}
        />
        <Button
          minimal
          small
          text="Rankings"
          onClick={() => navigate('/rankings')}
        />
        <div style={{ width: 1, height: 20, background: 'var(--border-subtle)', margin: '0 4px' }} />
        {user ? (
          <>
            <Button
              minimal
              small
              text="Admin"
              onClick={() => navigate('/admin')}
            />
            <Button minimal small text={`${user.display_name} (${user.role})`} />
            <Button minimal small text="Logout" onClick={logout} />
          </>
        ) : (
          <Button minimal small text="Login" onClick={() => navigate('/login')} />
        )}
      </div>
    </nav>
  );
}

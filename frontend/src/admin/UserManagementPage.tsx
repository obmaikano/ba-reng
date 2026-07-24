import { useEffect, useState, useCallback } from 'react';
import {
  Button, Spinner, Intent, Tag, Dialog, FormGroup, InputGroup, HTMLSelect,
} from '@blueprintjs/core';
import { get, post, put } from '../api';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface User {
  id: number;
  email: string;
  display_name: string;
  role: string;
  is_active: number;
  created_at: string;
  last_login_at: string | null;
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const MONO_XS: React.CSSProperties = {
  fontFamily: 'var(--font-mono)', fontSize: 10, color: '#738091',
};

const ROLE_COLORS: Record<string, string> = {
  admin: '#F55656',
  editor: '#D9822B',
  viewer: '#2B95D6',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function UserManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');

  // Add-user dialog state
  const [showAdd, setShowAdd] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState('editor');
  const [newPassword, setNewPassword] = useState('');
  const [adding, setAdding] = useState(false);
  const [addErr, setAddErr] = useState('');

  // Inline edit state
  const [editingRole, setEditingRole] = useState<Record<number, string>>({});

  const fetchUsers = useCallback(async () => {
    try {
      const data = await get<User[]>('/api/v1/admin/users');
      setUsers(data);
      setError('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleAddUser = async () => {
    setAddErr('');
    setAdding(true);
    try {
      await post('/api/v1/admin/users', {
        email: newEmail,
        display_name: newName,
        role: newRole,
        password: newPassword,
      });
      setShowAdd(false);
      setNewEmail(''); setNewName(''); setNewRole('editor'); setNewPassword('');
      setMsg('User created');
      fetchUsers();
    } catch (err: unknown) {
      setAddErr(err instanceof Error ? err.message : 'Failed');
    } finally {
      setAdding(false);
    }
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      await put(`/api/v1/admin/users/${userId}`, { role: newRole });
      setEditingRole((prev) => { const n = { ...prev }; delete n[userId]; return n; });
      setMsg('Role updated');
      fetchUsers();
    } catch (err: unknown) {
      setMsg(err instanceof Error ? err.message : 'Update failed');
    }
  };

  const handleToggleActive = async (userId: number, currentActive: boolean) => {
    try {
      await put(`/api/v1/admin/users/${userId}`, { is_active: !currentActive });
      setMsg(currentActive ? 'User deactivated' : 'User reactivated');
      fetchUsers();
    } catch (err: unknown) {
      setMsg(err instanceof Error ? err.message : 'Toggle failed');
    }
  };

  // -----------------------------------------------------------------------
  // States
  // -----------------------------------------------------------------------

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}><Spinner size={24} /></div>;
  }

  if (error) {
    return (
      <div style={{ color: '#F55656', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        {error}
        <Button minimal small intent={Intent.PRIMARY} onClick={fetchUsers} style={{ marginLeft: 12 }}>Retry</Button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 900 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h1 style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 600, color: '#E8EDF2', margin: 0 }}>
          User Management
          <span style={{ color: '#738091', fontSize: 13, fontWeight: 400, marginLeft: 10 }}>
            {users.length} users
          </span>
        </h1>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {msg && <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#15B371' }}>{msg}</span>}
          <Button small intent={Intent.PRIMARY} icon="plus" onClick={() => setShowAdd(true)}>
            Add User
          </Button>
        </div>
      </div>

      {/* User table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{
          width: '100%', borderCollapse: 'collapse',
          fontFamily: 'var(--font-mono)', fontSize: 11, color: '#BDC1C9',
        }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #1F242E' }}>
              <th style={{ textAlign: 'left', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Email</th>
              <th style={{ textAlign: 'left', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Name</th>
              <th style={{ textAlign: 'left', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Role</th>
              <th style={{ textAlign: 'left', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Status</th>
              <th style={{ textAlign: 'left', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Last Login</th>
              <th style={{ textAlign: 'right', padding: '8px 12px', color: '#738091', fontWeight: 500, fontSize: 10 }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} style={{ borderBottom: '1px solid #1A1F27', opacity: user.is_active ? 1 : 0.5 }}>
                <td style={{ padding: '8px 12px' }}>{user.email}</td>
                <td style={{ padding: '8px 12px' }}>{user.display_name}</td>
                <td style={{ padding: '8px 12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Tag minimal style={{
                      background: ROLE_COLORS[user.role] || '#BDC1C9',
                      color: '#0B0E14', fontSize: 10,
                    }}>
                      {user.role}
                    </Tag>
                    <HTMLSelect
                    minimal
                    value={editingRole[user.id] ?? user.role}
                    onChange={(e) => setEditingRole((prev) => ({ ...prev, [user.id]: e.target.value }))}
                    style={{
                      fontFamily: 'var(--font-mono)', fontSize: 10,
                      background: 'transparent', border: '1px solid #1F242E',
                      color: ROLE_COLORS[user.role] || '#BDC1C9',
                      padding: '2px 6px',
                    }}
                  >
                    <option value="admin">admin</option>
                    <option value="editor">editor</option>
                    <option value="viewer">viewer</option>
                  </HTMLSelect>
                  {editingRole[user.id] && editingRole[user.id] !== user.role && (
                    <Button
                      minimal small intent={Intent.PRIMARY}
                      onClick={() => handleRoleChange(user.id, editingRole[user.id])}
                      style={{ marginLeft: 6, fontSize: 10 }}
                    >
                      Save
                    </Button>
                    )}
                  </div>
                </td>
                <td style={{ padding: '8px 12px' }}>
                  <Tag minimal style={{
                    background: user.is_active ? '#15B371' : '#F55656',
                    color: '#0B0E14', fontSize: 10,
                  }}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </Tag>
                </td>
                <td style={{ padding: '8px 12px', ...MONO_XS }}>
                  {user.last_login_at
                    ? new Date(user.last_login_at + 'Z').toLocaleDateString()
                    : 'Never'}
                </td>
                <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                  <Button
                    minimal small
                    intent={user.is_active ? Intent.DANGER : Intent.SUCCESS}
                    onClick={() => handleToggleActive(user.id, !!user.is_active)}
                    style={{ fontSize: 10 }}
                  >
                    {user.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add User dialog */}
      <Dialog
        isOpen={showAdd}
        onClose={() => setShowAdd(false)}
        title="Add User"
        style={{ background: '#12161C', fontFamily: 'var(--font-mono)' }}
      >
        <div style={{ padding: '16px 20px' }}>
          <FormGroup label="Email" labelFor="new-email">
            <InputGroup
              id="new-email" type="email" value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="user@bareng.bw"
            />
          </FormGroup>
          <FormGroup label="Display Name" labelFor="new-name">
            <InputGroup
              id="new-name" value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Display Name"
            />
          </FormGroup>
          <FormGroup label="Role" labelFor="new-role">
            <HTMLSelect
              id="new-role" value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
            >
              <option value="editor">Editor</option>
              <option value="viewer">Viewer</option>
              <option value="admin">Admin</option>
            </HTMLSelect>
          </FormGroup>
          <FormGroup label="Password" labelFor="new-password">
            <InputGroup
              id="new-password" type="password" value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Min 8 characters"
            />
          </FormGroup>
          {addErr && <p style={{ color: '#F55656', fontSize: 11 }}>{addErr}</p>}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
            <Button minimal onClick={() => setShowAdd(false)}>Cancel</Button>
            <Button intent={Intent.PRIMARY} loading={adding} onClick={handleAddUser}>Create User</Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}

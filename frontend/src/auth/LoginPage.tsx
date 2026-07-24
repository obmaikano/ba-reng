import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Classes, FormGroup, InputGroup, Spinner, Intent } from '@blueprintjs/core';
import { useAuth } from './AuthContext';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
      navigate('/admin');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={Classes.DARK} style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-canvas, #0B0E14)',
    }}>
      <Card style={{ width: 380, padding: '2rem' }}>
        <h2 style={{
          fontFamily: 'var(--font-mono, monospace)', color: 'var(--text-secondary, #BDC1C9)',
          marginBottom: '1.5rem', fontSize: '1.1rem',
        }}>
          Ba Reng? Admin
        </h2>
        <form onSubmit={handleSubmit}>
          <FormGroup label="Email" labelFor="email">
            <InputGroup
              id="email" type="email" value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@bareng.bw" autoFocus
            />
          </FormGroup>
          <FormGroup label="Password" labelFor="password">
            <InputGroup
              id="password" type="password" value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
            />
          </FormGroup>
          {error && <p style={{ color: '#F55656', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</p>}
          <Button type="submit" intent={Intent.PRIMARY} fill loading={submitting}>
            {submitting ? <Spinner size={16} /> : 'Sign in'}
          </Button>
        </form>
      </Card>
    </div>
  );
}

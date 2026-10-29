'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { adminLogin, setAdminToken } from '../../../lib/api';

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const res = await adminLogin({ email, password });
      setAdminToken(res.access_token);
      router.push('/admin');
    } catch (err: any) {
      setError(err.message || 'Invalid administrative credentials');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '420px', paddingTop: '4rem' }}>
      <div className="card" style={{ border: '1px solid rgba(239, 68, 68, 0.3)' }}>
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div style={{
            display: 'inline-block',
            padding: '0.4rem 0.8rem',
            background: 'var(--danger-bg)',
            color: '#fca5a5',
            borderRadius: 'var(--radius-full)',
            fontSize: '0.75rem',
            fontWeight: 700,
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            marginBottom: '0.75rem',
          }}>
            Restricted Access
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Admin Portal</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Evocation platform administration and monitoring
          </p>
        </div>

        {error && (
          <div style={{
            background: 'var(--danger-bg)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: '#fca5a5',
            padding: '0.75rem',
            borderRadius: 'var(--radius-md)',
            marginBottom: '1.25rem',
            fontSize: '0.85rem',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Admin Email</label>
            <input
              type="email"
              required
              className="form-input"
              placeholder="admin@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              required
              className="form-input"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.5rem', background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' }}
          >
            {isLoading ? 'Verifying...' : 'Authorize Admin Session'}
          </button>
        </form>
      </div>
    </div>
  );
}

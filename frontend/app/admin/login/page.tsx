'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { adminLogin, setAdminToken } from '../../../lib/api';

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('admin@example.com');
  const [password, setPassword] = useState('AdminSecure123!');
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
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-800/80 p-8 shadow-2xl backdrop-blur-md">
        <div className="text-center mb-6">
          <Link href="/" className="inline-flex items-center gap-3 mb-4">
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500 font-bold text-white text-xl">
              P
            </span>
            <span className="text-left">
              <strong className="block text-2xl text-white">PRFLO</strong>
              <small className="text-[10px] uppercase tracking-widest text-slate-400">Admin Control</small>
            </span>
          </Link>
          <div className="mt-2 inline-block rounded-full bg-rose-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-rose-400 border border-rose-500/20">
            Restricted Staff Portal
          </div>
          <h1 className="mt-3 text-2xl font-bold text-white">Administrative Sign In</h1>
          <p className="mt-1 text-xs text-slate-400">
            Platform governance, user management, and Cloudflare DNS oversight
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Admin Email
            </label>
            <input
              type="email"
              required
              className="mt-1 block w-full rounded-xl border border-slate-700 bg-slate-900 px-3.5 py-3 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none text-sm"
              placeholder="admin@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300">
              Password
            </label>
            <input
              type="password"
              required
              className="mt-1 block w-full rounded-xl border border-slate-700 bg-slate-900 px-3.5 py-3 text-white placeholder-slate-500 focus:border-indigo-500 focus:outline-none text-sm"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-3 text-xs text-slate-400 space-y-1">
            <p className="font-semibold text-slate-300">Default Super-Admin Seed:</p>
            <p>Email: <code className="text-indigo-400">admin@example.com</code></p>
            <p>Password: <code className="text-indigo-400">AdminSecure123!</code></p>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-xl bg-indigo-600 px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
          >
            {isLoading ? 'Verifying Credentials...' : 'Authorize Admin Session →'}
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link href="/dashboard" className="text-xs text-slate-400 hover:text-white transition">
            ← Return to Customer Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

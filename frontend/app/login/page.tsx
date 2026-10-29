'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { loginUser, setAuthToken } from '../../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fillDemoCreds = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await loginUser({ email, password });
      setAuthToken(data.access_token);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-12 md:px-8 flex items-center justify-center">
      <div className="mx-auto max-w-6xl w-full overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-xl">
        <div className="grid md:grid-cols-2">
          {/* Left Hero Sidebar */}
          <aside className="hidden bg-slate-900 p-10 text-white md:flex md:flex-col md:justify-between">
            <div>
              <Link href="/" className="mb-8 flex items-center gap-3">
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500 font-bold">
                  P
                </span>
                <span>
                  <strong className="block text-2xl">Prflo</strong>
                  <small className="text-xs uppercase tracking-widest text-slate-300">by Evocation</small>
                </span>
              </Link>
              <h1 className="text-4xl font-black tracking-tight">
                Welcome back to your control panel.
              </h1>
            </div>

            <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5">
              <div className="flex items-center justify-between">
                <p className="text-xs uppercase tracking-widest text-slate-400">Demo credentials</p>
                <button
                  type="button"
                  onClick={() => fillDemoCreds('admin@example.com', 'AdminSecure123!')}
                  className="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium"
                >
                  Auto-fill
                </button>
              </div>
              <div className="mt-3 space-y-2 text-sm text-slate-200">
                <p><span className="text-slate-400">Email:</span> admin@example.com</p>
                <p><span className="text-slate-400">Password:</span> AdminSecure123!</p>
              </div>
            </div>
          </aside>

          {/* Right Login Form */}
          <main className="p-6 sm:p-10">
            <div className="mb-8 flex items-start justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">Sign in</p>
                <h2 className="mt-2 text-3xl font-bold text-slate-900">Access your dashboard</h2>
              </div>
              <Link href="/" className="text-sm text-slate-500 hover:text-slate-900">
                Home
              </Link>
            </div>

            {error && (
              <div className="mb-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                {error}
              </div>
            )}

            <form className="space-y-5" onSubmit={handleSubmit}>
              <label className="block text-sm font-medium text-slate-700">
                Email
                <input
                  className="mt-2 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                  type="email"
                  required
                  placeholder="demo@prflo.dev"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Password
                <input
                  className="mt-2 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                  type="password"
                  required
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>

              <div className="flex items-center justify-between text-sm text-slate-600">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="rounded border-slate-300 text-indigo-600"
                  />
                  <span>Remember me</span>
                </label>
                <a href="#" className="font-medium text-indigo-600 hover:underline">
                  Forgot password?
                </a>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="block w-full rounded-xl bg-indigo-600 px-4 py-3 text-center font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-600">
              New to Prflo?{' '}
              <Link href="/register" className="font-semibold text-indigo-600 hover:underline">
                Create an account
              </Link>
            </p>
          </main>
        </div>
      </div>
    </div>
  );
}

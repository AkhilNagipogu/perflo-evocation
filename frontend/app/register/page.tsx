'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { registerUser, loginUser, setAuthToken } from '../../lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreed, setAgreed] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!agreed) {
      setError('Please agree to the terms to continue.');
      return;
    }

    setIsLoading(true);

    try {
      await registerUser({
        email,
        username,
        full_name: fullName || undefined,
        password,
      });

      // Automatically log in after register
      try {
        const loginData = await loginUser({ email, password });
        setAuthToken(loginData.access_token);
        router.push('/dashboard');
      } catch {
        router.push('/login');
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed.');
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
                Claim a space for your next big idea.
              </h1>
            </div>

            <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5 text-sm text-slate-200">
              <p className="text-xs uppercase tracking-widest text-slate-400">Instant setup</p>
              <p className="mt-3">
                Explore subdomains, DNS management, and wallet credits in a streamlined environment.
              </p>
            </div>
          </aside>

          {/* Right Register Form */}
          <main className="p-6 sm:p-10">
            <div className="mb-8 flex items-start justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">Create account</p>
                <h2 className="mt-2 text-3xl font-bold text-slate-900">Start your own subdomain</h2>
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

            <form className="space-y-4" onSubmit={handleSubmit}>
              <label className="block text-sm font-medium text-slate-700">
                Full name
                <input
                  className="mt-2 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                  placeholder="Full name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Username
                <input
                  className="mt-2 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                  placeholder="Username"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value.toLowerCase().trim())}
                />
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Email
                <input
                  className="mt-2 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                  type="email"
                  placeholder="Email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Password
                <input
                  className="mt-2 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                  type="password"
                  placeholder="Enter your password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Confirm password
                <input
                  className="mt-2 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                  type="password"
                  placeholder="Confirm your password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </label>

              <label className="flex items-start gap-2 text-sm text-slate-600 cursor-pointer">
                <input
                  className="mt-1 rounded border-slate-300 text-indigo-600"
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                />
                <span>I agree to the terms of service and understand the subdomain rental policy.</span>
              </label>

              <button
                type="submit"
                disabled={isLoading}
                className="block w-full rounded-xl bg-indigo-600 px-4 py-3 text-center font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
              >
                {isLoading ? 'Creating account...' : 'Create account'}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate-600">
              Already have an account?{' '}
              <Link href="/login" className="font-semibold text-indigo-600 hover:underline">
                Sign in
              </Link>
            </p>
          </main>
        </div>
      </div>
    </div>
  );
}

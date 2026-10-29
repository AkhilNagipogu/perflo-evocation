'use client';

import { useState, useEffect } from 'react';
import { getCurrentUser } from '../../../lib/api';

export default function SettingsPage() {
  const [fullName, setFullName] = useState('Akhil N.');
  const [username, setUsername] = useState('akhil');
  const [email, setEmail] = useState('demo@prflo.dev');

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [emailNotifications, setEmailNotifications] = useState(true);
  const [expiryReminders, setExpiryReminders] = useState(true);
  const [lowBalanceAlerts, setLowBalanceAlerts] = useState(true);

  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadUser() {
      try {
        const u = await getCurrentUser();
        if (u) {
          if (u.full_name) setFullName(u.full_name);
          if (u.username) setUsername(u.username);
          if (u.email) setEmail(u.email);
        }
      } catch {
        // demo defaults
      }
    }
    loadUser();
  }, []);

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMessage('Profile preferences updated successfully.');
    setTimeout(() => setStatusMessage(null), 3000);
  };

  return (
    <>
      <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-8">
        <p className="text-sm uppercase tracking-widest text-slate-400">Dashboard</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">Settings</h1>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        {statusMessage && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
            {statusMessage}
          </div>
        )}

        {/* Profile Card */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Profile</h2>
          <form onSubmit={handleSaveProfile} className="mt-5">
            <div className="grid gap-4 md:grid-cols-3">
              <input
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                aria-label="Full name"
                placeholder="Full name"
              />
              <input
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                aria-label="Username"
                placeholder="Username"
              />
              <input
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-label="Email"
                placeholder="Email address"
              />
            </div>
            <button
              type="submit"
              className="mt-5 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500"
            >
              Save profile
            </button>
          </form>
        </section>

        {/* Security and Preferences Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Security */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Security</h2>
            <div className="mt-4 space-y-3">
              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                type="password"
                placeholder="Current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                type="password"
                placeholder="New password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                type="password"
                placeholder="Confirm new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
            <p className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              This is a simulated password-change action and not a secure production authentication flow.
            </p>
          </section>

          {/* Preferences */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Preferences</h2>
            <div className="mt-4 space-y-4">
              <label className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm cursor-pointer">
                <span>Email notifications</span>
                <input
                  type="checkbox"
                  checked={emailNotifications}
                  onChange={(e) => setEmailNotifications(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-0"
                />
              </label>
              <label className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm cursor-pointer">
                <span>Rental-expiry reminders</span>
                <input
                  type="checkbox"
                  checked={expiryReminders}
                  onChange={(e) => setExpiryReminders(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-0"
                />
              </label>
              <label className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm cursor-pointer">
                <span>Low-balance notifications</span>
                <input
                  type="checkbox"
                  checked={lowBalanceAlerts}
                  onChange={(e) => setLowBalanceAlerts(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-0"
                />
              </label>
            </div>
          </section>
        </div>

        {/* Account Deletion */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Account</h2>
          <button
            onClick={() => alert('Account closure request has been recorded.')}
            className="mt-4 rounded-xl border border-rose-200 px-4 py-2.5 text-sm font-semibold text-rose-600 hover:bg-rose-50"
          >
            Request account closure
          </button>
        </section>
      </main>
    </>
  );
}

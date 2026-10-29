'use client';

import { useState, useEffect } from 'react';
import { getAdminStats } from '../../lib/api';

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const s = await getAdminStats();
        setStats(s);
      } catch {
        // Fallback for mock demo
      }
    }
    loadStats();
  }, []);

  const totalUsers = stats?.total_users != null ? stats.total_users.toLocaleString() : '2,480';
  const activeRentals = stats?.active_rentals != null ? stats.active_rentals.toLocaleString() : '1,248';
  const walletVolume = stats?.total_wallet_balance_paise != null
    ? `₹${Math.floor(stats.total_wallet_balance_paise / 100).toLocaleString()}`
    : '₹5,300';
  const dnsChanges = stats?.total_dns_records != null ? stats.total_dns_records.toLocaleString() : '113';

  return (
    <>
      <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-8">
        <p className="text-sm uppercase tracking-widest text-slate-400">Dashboard</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">Admin demo</h1>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Admin demo</h2>
          <p className="mt-2 text-sm text-slate-500">
            This area is clearly separated from the customer dashboard and is intended for mock administration only.
          </p>
        </section>

        {/* 4 Metrics Grid */}
        <div className="grid gap-4 md:grid-cols-4">
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Users</p>
            <p className="mt-4 text-3xl font-bold text-slate-900">{totalUsers}</p>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Active rentals</p>
            <p className="mt-4 text-3xl font-bold text-slate-900">{activeRentals}</p>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Wallet volume</p>
            <p className="mt-4 text-3xl font-bold text-slate-900">{walletVolume}</p>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">DNS changes today</p>
            <p className="mt-4 text-3xl font-bold text-slate-900">{dnsChanges}</p>
          </article>
        </div>

        {/* 2-Column Overview and Activity */}
        <div className="grid gap-6 xl:grid-cols-2">
          {/* User overview */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">User overview</h2>
            <div className="mt-4 space-y-3">
              <p className="flex justify-between items-center rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-900">
                <span className="font-medium">rahul.evocation.in</span>
                <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs text-emerald-700 font-medium">
                  active
                </span>
              </p>
              <p className="flex justify-between items-center rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-900">
                <span className="font-medium">project.evocation.in</span>
                <span className="rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-700 font-medium">
                  expiring soon
                </span>
              </p>
            </div>
          </section>

          {/* Activity log */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Activity log</h2>
            <div className="mt-4 space-y-3">
              <p className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-900">
                <strong className="block text-slate-900">Wallet top-up of ₹50 completed</strong>
                <span className="mt-1 block text-xs text-slate-500">9 days ago</span>
              </p>
              <p className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-900">
                <strong className="block text-slate-900">rahul.evocation.in activated</strong>
                <span className="mt-1 block text-xs text-slate-500">18 days ago</span>
              </p>
              <p className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-900">
                <strong className="block text-slate-900">DNS record updated for rahul.evocation.in</strong>
                <span className="mt-1 block text-xs text-slate-500">2 days ago</span>
              </p>
            </div>
          </section>
        </div>
      </main>
    </>
  );
}

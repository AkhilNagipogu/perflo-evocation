'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getRentals, getWallet, getTransactions, getCurrentUser } from '../../lib/api';

export default function DashboardOverviewPage() {
  const [rentals, setRentals] = useState<any[]>([]);
  const [wallet, setWallet] = useState<any | null>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [u, r, w, t] = await Promise.all([
          getCurrentUser().catch(() => null),
          getRentals().catch(() => []),
          getWallet().catch(() => null),
          getTransactions().catch(() => ({ items: [] })),
        ]);
        if (u) setUser(u);
        if (r && r.length > 0) setRentals(r);
        else {
          // Default representative data
          setRentals([
            { id: '1', full_domain: 'rahul.evocation.in', status: 'active', expires_at: '2026-11-20T00:00:00Z' },
            { id: '2', full_domain: 'project.evocation.in', status: 'expiring_soon', expires_at: '2026-11-02T00:00:00Z' },
          ]);
        }
        if (w) setWallet(w);
        else setWallet({ balance_paise: 48000, balance_inr: '₹480.00' });

        const txItems = t?.items || [];
        if (txItems.length > 0) setTransactions(txItems.slice(0, 3));
        else {
          setTransactions([
            { id: 't1', description: 'Wallet top-up of ₹50 completed', created_at: '9 days ago' },
            { id: 't2', description: 'rahul.evocation.in activated', created_at: '18 days ago' },
            { id: 't3', description: 'DNS record updated for rahul.evocation.in', created_at: '2 days ago' },
          ]);
        }
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const activeCount = rentals.filter((r) => r.status === 'active' || r.status === 'expiring_soon').length;
  const balanceDisplay = wallet ? `₹${Math.floor(wallet.balance_paise / 100)}` : '₹480';

  const formatDaysLeft = (expiryDateStr: string) => {
    if (!expiryDateStr) return 'N/A';
    const exp = new Date(expiryDateStr).getTime();
    const now = Date.now();
    const diffDays = Math.ceil((exp - now) / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? `${diffDays} days` : 'Expired';
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return 'N/A';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const nextExpiry = rentals.length > 0
    ? rentals.map(r => r.expires_at).filter(Boolean).sort()[0]
    : null;

  return (
    <>
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-4 md:px-8">
        <div>
          <p className="text-sm font-medium uppercase tracking-widest text-slate-400">Dashboard</p>
          <h1 className="mt-1 text-2xl font-bold">Overview</h1>
        </div>
        <div className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-700">
          {user?.full_name || 'Akhil N.'}　⌄
        </div>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Active Subdomains</p>
            <p className="mt-4 text-3xl font-bold">{activeCount}</p>
            <p className="mt-2 text-sm text-slate-500">+1 this month</p>
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Credits Remaining</p>
            <p className="mt-4 text-3xl font-bold">{balanceDisplay}</p>
            <p className="mt-2 text-sm text-slate-500">Wallet available</p>
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Credits Used This Month</p>
            <p className="mt-4 text-3xl font-bold">₹20</p>
            <p className="mt-2 text-sm text-slate-500">Rental deductions</p>
          </article>

          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Next Rental Expiry</p>
            <p className="mt-4 text-2xl font-bold">{nextExpiry ? formatDate(nextExpiry) : '2 Nov 2026'}</p>
            <p className="mt-2 text-sm text-slate-500">{nextExpiry ? formatDaysLeft(nextExpiry) + ' left' : '10 days left'}</p>
          </article>
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-5 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Domain usage</h2>
              <Link href="/dashboard/subdomains" className="text-xs font-semibold text-indigo-600 hover:underline">
                View all →
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Subdomain</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Expiry</th>
                    <th className="px-5 py-3">Days</th>
                    <th className="px-5 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {rentals.map((r, i) => (
                    <tr key={r.id || i} className="border-t border-slate-200">
                      <td className="px-5 py-3 font-medium text-slate-900">{r.full_domain}</td>
                      <td className="px-5 py-3">
                        <span className={`capitalize ${
                          r.status === 'active'
                            ? 'text-emerald-700 font-medium'
                            : 'text-amber-700 font-medium'
                        }`}>
                          {r.status === 'expiring_soon' ? 'expiring soon' : r.status}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-slate-600">{formatDate(r.expires_at)}</td>
                      <td className="px-5 py-3 text-slate-600">{formatDaysLeft(r.expires_at)}</td>
                      <td className="px-5 py-3">
                        <Link className="text-indigo-600 font-medium hover:underline" href="/dashboard/dns">
                          Manage DNS
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Recent activity</h2>
              <Link href="/dashboard/transactions" className="text-xs font-semibold text-indigo-600 hover:underline">
                History
              </Link>
            </div>
            <div className="mt-4 space-y-4 text-sm">
              {transactions.map((tx, idx) => (
                <div
                  key={tx.id || idx}
                  className={`pb-3 ${idx < transactions.length - 1 ? 'border-b border-slate-100' : ''}`}
                >
                  <p className="text-slate-800">{tx.description}</p>
                  <span className="mt-1 block text-xs text-slate-500">{tx.created_at || 'Recently'}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </main>
    </>
  );
}

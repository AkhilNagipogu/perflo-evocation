'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  getAdminStats,
  adminListRentals,
  adminManageRental,
  adminListUsers,
  adminManageUser,
  adminAdjustWallet,
  adminListCoupons,
  adminCreateCoupon,
  adminListAbuseReports,
  adminReviewAbuseReport,
  adminGetAuditLogs,
  getAdminToken,
} from '../../lib/api';

type Tab = 'overview' | 'rentals' | 'users' | 'coupons' | 'abuse' | 'audit';

export default function AdminPage() {
  const [stats, setStats] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [isAdminAuthed, setIsAdminAuthed] = useState(false);

  // Data states
  const [rentals, setRentals] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [coupons, setCoupons] = useState<any[]>([]);
  const [abuseReports, setAbuseReports] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);

  // Adjustment & Form States
  const [adjustUserId, setAdjustUserId] = useState('');
  const [adjustAmount, setAdjustAmount] = useState(50);
  const [adjustReason, setAdjustReason] = useState('Administrative top-up');
  const [newCouponCode, setNewCouponCode] = useState('');
  const [newCouponDiscount, setNewCouponDiscount] = useState(10);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  useEffect(() => {
    const token = getAdminToken();
    setIsAdminAuthed(!!token);

    async function loadData() {
      try {
        const s = await getAdminStats();
        setStats(s);

        if (token) {
          const [r, u, c, a, logs] = await Promise.all([
            adminListRentals().catch(() => []),
            adminListUsers().catch(() => []),
            adminListCoupons().catch(() => []),
            adminListAbuseReports().catch(() => []),
            adminGetAuditLogs().catch(() => ({ items: [] })),
          ]);
          setRentals(r || []);
          setUsers(u || []);
          setCoupons(c || []);
          setAbuseReports(a || []);
          setAuditLogs(logs?.items || []);
        }
      } catch {
        // Fallback demo values
      }
    }
    loadData();
  }, [activeTab]);

  const handleRentalAction = async (rentalId: string, action: string) => {
    const reason = prompt(`Enter reason for ${action}:`, 'Administrative action');
    if (!reason) return;
    try {
      await adminManageRental(rentalId, action, reason);
      setActionNotice(`Rental ${action} applied successfully.`);
      const r = await adminListRentals();
      setRentals(r);
      setTimeout(() => setActionNotice(null), 3500);
    } catch (err: any) {
      alert(err.message || 'Action failed');
    }
  };

  const handleUserAction = async (userId: string, action: string) => {
    const reason = prompt(`Enter reason for ${action}:`, 'Administrative policy');
    if (!reason) return;
    try {
      await adminManageUser(userId, action, reason);
      setActionNotice(`User updated: ${action}`);
      const u = await adminListUsers();
      setUsers(u);
      setTimeout(() => setActionNotice(null), 3500);
    } catch (err: any) {
      alert(err.message || 'Action failed');
    }
  };

  const handleWalletAdjust = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjustUserId) return;
    try {
      await adminAdjustWallet(adjustUserId, Math.round(adjustAmount * 100), adjustReason);
      setActionNotice(`Credited ₹${adjustAmount} to user wallet.`);
      setAdjustAmount(50);
      const u = await adminListUsers();
      setUsers(u);
      setTimeout(() => setActionNotice(null), 3500);
    } catch (err: any) {
      alert(err.message || 'Wallet adjustment failed');
    }
  };

  const handleCreateCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCouponCode.trim()) return;
    try {
      await adminCreateCoupon({
        code: newCouponCode.trim().toUpperCase(),
        discount_type: 'percentage',
        discount_value: Number(newCouponDiscount),
        max_uses: 100,
      });
      setActionNotice(`Coupon ${newCouponCode.toUpperCase()} created!`);
      setNewCouponCode('');
      const c = await adminListCoupons();
      setCoupons(c);
      setTimeout(() => setActionNotice(null), 3500);
    } catch (err: any) {
      alert(err.message || 'Failed to create coupon');
    }
  };

  const handleReviewAbuse = async (reportId: string, action: string) => {
    const notes = prompt(`Review notes for ${action}:`, 'Verified by compliance');
    if (!notes) return;
    try {
      await adminReviewAbuseReport(reportId, { action, notes });
      setActionNotice(`Abuse report updated: ${action}`);
      const a = await adminListAbuseReports();
      setAbuseReports(a);
      setTimeout(() => setActionNotice(null), 3500);
    } catch (err: any) {
      alert(err.message || 'Failed to update abuse report');
    }
  };

  const totalUsers = stats?.total_users != null ? stats.total_users.toLocaleString() : '2,480';
  const activeRentals = stats?.active_rentals != null ? stats.active_rentals.toLocaleString() : '1,248';
  const walletVolume = stats?.total_wallet_balance_paise != null
    ? `₹${Math.floor(stats.total_wallet_balance_paise / 100).toLocaleString()}`
    : '₹5,300';
  const dnsChanges = stats?.total_dns_records != null ? stats.total_dns_records.toLocaleString() : '113';

  return (
    <>
      <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-widest text-slate-400">Control Panel</p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">Admin Dashboard</h1>
        </div>

        <div className="flex items-center gap-3">
          {!isAdminAuthed ? (
            <Link
              href="/admin/login"
              className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition"
            >
              Sign In to Admin Portal →
            </Link>
          ) : (
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              Super Admin Session Active
            </span>
          )}
        </div>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        {actionNotice && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
            {actionNotice}
          </div>
        )}

        {/* Top 4 Metrics Cards (Matches JUst html/admin.html) */}
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

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 space-x-2 overflow-x-auto text-sm font-medium">
          {(['overview', 'rentals', 'users', 'coupons', 'abuse', 'audit'] as Tab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 capitalize border-b-2 transition whitespace-nowrap ${
                activeTab === tab
                  ? 'border-indigo-600 text-indigo-600 font-semibold'
                  : 'border-transparent text-slate-500 hover:text-slate-900'
              }`}
            >
              {tab === 'overview'
                ? 'Overview & Activity'
                : tab === 'users'
                ? 'Users & Wallets'
                : tab === 'abuse'
                ? 'Abuse Reports'
                : tab === 'audit'
                ? 'Audit Logs'
                : tab}
            </button>
          ))}
        </div>

        {/* Tab Content 1: Overview & Activity (Matches JUst html/admin.html) */}
        {activeTab === 'overview' && (
          <div className="grid gap-6 xl:grid-cols-2">
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
        )}

        {/* Tab Content 2: Rentals Management */}
        {activeTab === 'rentals' && (
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">Live Subdomain Rentals</h2>
              <span className="text-xs text-slate-500">{rentals.length} active or recorded rentals</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Subdomain</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Auto Renew</th>
                    <th className="px-5 py-3">Expires At</th>
                    <th className="px-5 py-3">Admin Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {rentals.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-5 py-8 text-center text-slate-500">
                        {isAdminAuthed ? 'No rentals found in database.' : 'Please sign in to the Admin Portal to view live rentals.'}
                      </td>
                    </tr>
                  ) : (
                    rentals.map((r) => (
                      <tr key={r.id} className="border-t border-slate-200 hover:bg-slate-50/50">
                        <td className="px-5 py-4 font-mono font-medium text-slate-900">{r.full_domain}</td>
                        <td className="px-5 py-4">
                          <span className="inline-block rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800">
                            {r.status}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-slate-600">{r.auto_renew ? 'Yes' : 'No'}</td>
                        <td className="px-5 py-4 text-slate-600">
                          {r.expires_at ? new Date(r.expires_at).toLocaleDateString() : 'N/A'}
                        </td>
                        <td className="px-5 py-4 space-x-2">
                          <button
                            onClick={() => handleRentalAction(r.id, 'renew')}
                            className="text-xs font-semibold text-indigo-600 hover:underline"
                          >
                            Extend (+1yr)
                          </button>
                          <button
                            onClick={() => handleRentalAction(r.id, 'quarantine')}
                            className="text-xs font-semibold text-amber-600 hover:underline"
                          >
                            Quarantine
                          </button>
                          <button
                            onClick={() => handleRentalAction(r.id, 'cancel')}
                            className="text-xs font-semibold text-rose-600 hover:underline"
                          >
                            Cancel
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Tab Content 3: Users & Wallet Adjustments */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Manual Wallet Adjustment</h2>
              <form onSubmit={handleWalletAdjust} className="mt-4 grid gap-3 sm:grid-cols-4 items-end">
                <div>
                  <label className="block text-xs font-medium text-slate-700">Select User ID / Email</label>
                  <select
                    className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900"
                    value={adjustUserId}
                    onChange={(e) => setAdjustUserId(e.target.value)}
                  >
                    <option value="">-- Choose User --</option>
                    {users.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.username} ({u.email})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700">Amount (₹)</label>
                  <input
                    type="number"
                    min="1"
                    className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900"
                    value={adjustAmount}
                    onChange={(e) => setAdjustAmount(Number(e.target.value))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700">Audit Reason</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900"
                    value={adjustReason}
                    onChange={(e) => setAdjustReason(e.target.value)}
                  />
                </div>
                <button
                  type="submit"
                  className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
                >
                  Apply Credit ＋
                </button>
              </form>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
              <div className="p-5 border-b border-slate-100">
                <h2 className="text-lg font-semibold text-slate-900">Registered Users</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-5 py-3">Username</th>
                      <th className="px-5 py-3">Email</th>
                      <th className="px-5 py-3">Wallet Balance</th>
                      <th className="px-5 py-3">Status</th>
                      <th className="px-5 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-5 py-8 text-center text-slate-500">
                          {isAdminAuthed ? 'No users found.' : 'Sign in to Admin Portal to load users.'}
                        </td>
                      </tr>
                    ) : (
                      users.map((u) => (
                        <tr key={u.id} className="border-t border-slate-200 hover:bg-slate-50/50">
                          <td className="px-5 py-4 font-medium text-slate-900">{u.username}</td>
                          <td className="px-5 py-4 text-slate-600">{u.email}</td>
                          <td className="px-5 py-4 font-semibold text-emerald-600">
                            ₹{u.wallet ? (u.wallet.balance_paise / 100).toFixed(2) : '0.00'}
                          </td>
                          <td className="px-5 py-4">
                            <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${
                              u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                            }`}>
                              {u.is_active ? 'Active' : 'Suspended'}
                            </span>
                          </td>
                          <td className="px-5 py-4 space-x-2">
                            {u.is_active ? (
                              <button
                                onClick={() => handleUserAction(u.id, 'ban')}
                                className="text-xs font-semibold text-rose-600 hover:underline"
                              >
                                Suspend User
                              </button>
                            ) : (
                              <button
                                onClick={() => handleUserAction(u.id, 'unban')}
                                className="text-xs font-semibold text-emerald-600 hover:underline"
                              >
                                Activate
                              </button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {/* Tab Content 4: Coupons */}
        {activeTab === 'coupons' && (
          <div className="space-y-6">
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Create New Coupon</h2>
              <form onSubmit={handleCreateCoupon} className="mt-4 flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  required
                  placeholder="CODE (e.g. LAUNCH20)"
                  className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900 font-mono uppercase"
                  value={newCouponCode}
                  onChange={(e) => setNewCouponCode(e.target.value)}
                />
                <input
                  type="number"
                  min="1"
                  max="100"
                  required
                  placeholder="Discount %"
                  className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-900"
                  value={newCouponDiscount}
                  onChange={(e) => setNewCouponDiscount(Number(e.target.value))}
                />
                <button
                  type="submit"
                  className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
                >
                  Create Promo Code
                </button>
              </form>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
              <div className="p-5 border-b border-slate-100">
                <h2 className="text-lg font-semibold text-slate-900">Active Promo Codes</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-5 py-3">Code</th>
                      <th className="px-5 py-3">Discount</th>
                      <th className="px-5 py-3">Uses</th>
                      <th className="px-5 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {coupons.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-5 py-8 text-center text-slate-500">
                          {isAdminAuthed ? 'No coupons found.' : 'Sign in to Admin Portal to load coupons.'}
                        </td>
                      </tr>
                    ) : (
                      coupons.map((c) => (
                        <tr key={c.id} className="border-t border-slate-200">
                          <td className="px-5 py-4 font-mono font-bold text-slate-900">{c.code}</td>
                          <td className="px-5 py-4">{c.discount_value}%</td>
                          <td className="px-5 py-4">{c.current_uses} / {c.max_uses || '∞'}</td>
                          <td className="px-5 py-4">
                            <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-800 font-semibold">
                              {c.is_active ? 'Active' : 'Expired'}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}

        {/* Tab Content 5: Abuse Reports */}
        {activeTab === 'abuse' && (
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100">
              <h2 className="text-lg font-semibold text-slate-900">Incident & Abuse Reports</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Reported Domain</th>
                    <th className="px-5 py-3">Category</th>
                    <th className="px-5 py-3">Status</th>
                    <th className="px-5 py-3">Reporter</th>
                    <th className="px-5 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {abuseReports.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-5 py-8 text-center text-slate-500">
                        {isAdminAuthed ? 'No pending abuse reports.' : 'Sign in to Admin Portal to load abuse reports.'}
                      </td>
                    </tr>
                  ) : (
                    abuseReports.map((a) => (
                      <tr key={a.id} className="border-t border-slate-200">
                        <td className="px-5 py-4 font-mono font-bold text-slate-900">{a.reported_domain}</td>
                        <td className="px-5 py-4 uppercase text-xs font-semibold text-slate-700">{a.category}</td>
                        <td className="px-5 py-4">
                          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-800 font-semibold">
                            {a.status}
                          </span>
                        </td>
                        <td className="px-5 py-4 text-slate-600">{a.reporter_email || 'Anonymous'}</td>
                        <td className="px-5 py-4 space-x-2">
                          <button
                            onClick={() => handleReviewAbuse(a.id, 'quarantine')}
                            className="text-xs font-semibold text-rose-600 hover:underline"
                          >
                            Quarantine Domain
                          </button>
                          <button
                            onClick={() => handleReviewAbuse(a.id, 'dismiss')}
                            className="text-xs font-semibold text-slate-600 hover:underline"
                          >
                            Dismiss
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Tab Content 6: Audit Logs */}
        {activeTab === 'audit' && (
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
            <div className="p-5 border-b border-slate-100">
              <h2 className="text-lg font-semibold text-slate-900">System Audit Trail</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500">
                  <tr>
                    <th className="px-5 py-3">Timestamp</th>
                    <th className="px-5 py-3">Action</th>
                    <th className="px-5 py-3">Actor</th>
                    <th className="px-5 py-3">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-5 py-8 text-center text-slate-500">
                        {isAdminAuthed ? 'No audit entries found.' : 'Sign in to Admin Portal to load audit logs.'}
                      </td>
                    </tr>
                  ) : (
                    auditLogs.map((log: any) => (
                      <tr key={log.id} className="border-t border-slate-200">
                        <td className="px-5 py-4 text-slate-600 text-xs">
                          {log.created_at ? new Date(log.created_at).toLocaleString() : 'Recent'}
                        </td>
                        <td className="px-5 py-4 font-mono text-xs font-semibold text-slate-900">{log.action}</td>
                        <td className="px-5 py-4 text-slate-700">{log.actor_user_id || 'System'}</td>
                        <td className="px-5 py-4 text-slate-600">{log.reason || 'Automated policy'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
    </>
  );
}

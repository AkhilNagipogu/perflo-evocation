'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getRentals, getParentDomains, getPricingPlans, purchaseRental, releaseRental, renameRental, renewRental } from '../../../lib/api';

export default function SubdomainsPage() {
  const [rentals, setRentals] = useState<any[]>([]);
  const [parentDomains, setParentDomains] = useState<any[]>([]);
  const [pricingPlans, setPricingPlans] = useState<any[]>([]);
  const [newName, setNewName] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Rename modal state
  const [renameRentalId, setRenameRentalId] = useState<string | null>(null);
  const [renameTargetName, setRenameTargetName] = useState('');
  const [isRenaming, setIsRenaming] = useState(false);

  const loadData = async () => {
    try {
      const [r, p, plans] = await Promise.all([
        getRentals().catch(() => []),
        getParentDomains().catch(() => []),
        getPricingPlans().catch(() => []),
      ]);
      if (r && r.length > 0) setRentals(r);
      else {
        setRentals([
          {
            id: 'demo-1',
            full_domain: 'rahul.evocation.in',
            subdomain_name: 'rahul',
            status: 'active',
            started_at: '2026-10-05T00:00:00Z',
            expires_at: '2026-11-20T00:00:00Z',
          },
          {
            id: 'demo-2',
            full_domain: 'project.evocation.in',
            subdomain_name: 'project',
            status: 'expiring_soon',
            started_at: '2026-09-13T00:00:00Z',
            expires_at: '2026-11-02T00:00:00Z',
          },
        ]);
      }
      setParentDomains(p);
      setPricingPlans(plans);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    setActionError(null);
    setActionSuccess(null);

    const parentId = parentDomains[0]?.id;
    const planId = pricingPlans[0]?.id;
    if (!parentId || !planId) {
      setActionError('Parent domain or pricing plan not loaded yet.');
      return;
    }

    try {
      await purchaseRental({
        subdomain_name: newName.trim().toLowerCase(),
        parent_domain_id: parentId,
        pricing_plan_id: planId,
      });
      setActionSuccess(`Successfully rented ${newName.trim().toLowerCase()}.${parentDomains[0].domain}`);
      setNewName('');
      loadData();
    } catch (err: any) {
      setActionError(err.message || 'Failed to rent subdomain');
    }
  };

  const handleRenew = async (rentalId: string, domainName: string) => {
    setActionError(null);
    setActionSuccess(null);
    try {
      await renewRental(rentalId);
      setActionSuccess(`Subdomain ${domainName} successfully renewed!`);
      loadData();
    } catch (err: any) {
      setActionError(err.message || 'Failed to renew subdomain');
    }
  };

  const handleRelease = async (rentalId: string, domainName: string) => {
    if (!confirm(`Are you sure you want to release ${domainName}? This will de-provision DNS records and make the name available to others.`)) {
      return;
    }
    setActionError(null);
    setActionSuccess(null);
    try {
      await releaseRental(rentalId);
      setActionSuccess(`Subdomain ${domainName} has been released.`);
      loadData();
    } catch (err: any) {
      setActionError(err.message || 'Failed to release subdomain');
    }
  };

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renameRentalId || !renameTargetName.trim()) return;
    setIsRenaming(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      await renameRental(renameRentalId, renameTargetName.trim().toLowerCase());
      setActionSuccess(`Subdomain renamed to ${renameTargetName.trim().toLowerCase()}`);
      setRenameRentalId(null);
      setRenameTargetName('');
      loadData();
    } catch (err: any) {
      setActionError(err.message || 'Failed to rename subdomain (must observe 24h cooldown)');
    } finally {
      setIsRenaming(false);
    }
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

  const formatDaysRemaining = (expiryDateStr: string) => {
    if (!expiryDateStr) return 'N/A';
    const exp = new Date(expiryDateStr).getTime();
    const now = Date.now();
    const diffDays = Math.ceil((exp - now) / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? `${diffDays} days remaining` : 'Grace period / Expired';
  };

  return (
    <>
      <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-8">
        <p className="text-sm uppercase tracking-widest text-slate-400">Dashboard</p>
        <h1 className="mt-1 text-2xl font-bold">My Subdomains</h1>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        {actionError && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {actionError}
          </div>
        )}
        {actionSuccess && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
            {actionSuccess}
          </div>
        )}

        <section className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold">My Subdomains</h2>
            <p className="text-sm text-slate-500">Rent and manage custom subdomains attached to your subscription bundle.</p>
          </div>
          <form onSubmit={handleRent} className="flex flex-col gap-2 sm:flex-row">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value.toLowerCase())}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-indigo-500"
              placeholder="new-name"
              required
            />
            <button
              type="submit"
              className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 whitespace-nowrap"
            >
              Rent a Subdomain
            </button>
          </form>
        </section>

        {rentals.map((r) => {
          const isExpiring = r.status === 'expiring_soon' || (r.expires_at && (new Date(r.expires_at).getTime() - Date.now()) < 1000 * 60 * 60 * 24 * 7);
          return (
            <article key={r.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-slate-900">{r.full_domain}</h2>
                  <div className="mt-2 flex gap-2">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize ${
                      r.status === 'active'
                        ? 'bg-emerald-100 text-emerald-700'
                        : isExpiring
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-slate-100 text-slate-700'
                    }`}>
                      {r.status === 'expiring_soon' ? 'expiring soon' : r.status}
                    </span>
                    <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700">
                      {formatDaysRemaining(r.expires_at)}
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Link
                    href={`/dashboard/dns?subdomain=${encodeURIComponent(r.full_domain)}`}
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Manage DNS
                  </Link>
                  <button
                    onClick={() => {
                      setRenameRentalId(r.id);
                      setRenameTargetName(r.subdomain_name || '');
                    }}
                    className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Change Subdomain
                  </button>
                  <button
                    onClick={() => handleRenew(r.id, r.full_domain)}
                    className="rounded-xl bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
                  >
                    Renew / Reactivate
                  </button>
                  <button
                    onClick={() => handleRelease(r.id, r.full_domain)}
                    className="rounded-xl border border-rose-200 bg-white px-3 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50"
                  >
                    Release Subdomain
                  </button>
                </div>
              </div>

              <div className="mt-5 grid gap-4 text-sm text-slate-600 md:grid-cols-3">
                <p>
                  <span className="block text-slate-400">Rental start</span>
                  <strong className="text-slate-800">{formatDate(r.started_at || r.created_at)}</strong>
                </p>
                <p>
                  <span className="block text-slate-400">Rental expiry</span>
                  <strong className="text-slate-800">{formatDate(r.expires_at)}</strong>
                </p>
                <p>
                  <span className="block text-slate-400">Days remaining</span>
                  <strong className="text-slate-800">{formatDaysRemaining(r.expires_at)}</strong>
                </p>
              </div>
            </article>
          );
        })}

        {/* Rename Modal */}
        {renameRentalId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
            <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
              <h3 className="text-lg font-bold text-slate-900">Change Subdomain Name</h3>
              <p className="mt-2 text-xs text-slate-500">
                Preserves your original expiration date and settings. Subject to a 24-hour rename cooldown.
              </p>
              <form onSubmit={handleRenameSubmit} className="mt-4 space-y-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500">
                    New Subdomain Label
                  </label>
                  <input
                    type="text"
                    value={renameTargetName}
                    onChange={(e) => setRenameTargetName(e.target.value.toLowerCase())}
                    className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-indigo-500"
                    placeholder="my-new-name"
                    required
                  />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setRenameRentalId(null)}
                    className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isRenaming}
                    className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
                  >
                    {isRenaming ? 'Renaming...' : 'Confirm Rename'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </>
  );
}

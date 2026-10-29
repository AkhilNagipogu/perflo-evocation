'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { getWallet, getCurrentUser, logout } from '../../lib/api';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [wallet, setWallet] = useState<any | null>(null);
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const u = await getCurrentUser();
        setUser(u);
        const w = await getWallet();
        setWallet(w);
      } catch (err) {
        // Fallback for demo
        setUser({ full_name: 'Akhil N.', username: 'akhil', email: 'akhil@example.com' });
        setWallet({ balance_paise: 48000, balance_inr: '₹480.00' });
      }
    }
    loadData();
  }, [pathname]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const navItemClass = (path: string) => {
    const isActive = pathname === path;
    return `block rounded-xl px-3 py-2.5 text-sm transition ${
      isActive
        ? 'bg-indigo-500/20 text-indigo-100 font-semibold'
        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
    }`;
  };

  const balanceDisplay = wallet
    ? `₹${Math.floor(wallet.balance_paise / 100)}`
    : '₹480';

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <aside className="hidden w-[250px] flex-shrink-0 bg-slate-900 text-white md:flex md:flex-col">
        <div className="p-5">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500 font-bold">
              P
            </span>
            <span>
              <strong className="block text-xl">PRFLO</strong>
              <small className="text-[10px] uppercase tracking-widest text-slate-400">by Evocation</small>
            </span>
          </Link>
        </div>

        <p className="px-4 py-2 text-xs font-semibold uppercase tracking-widest text-slate-400">Main</p>
        <nav className="space-y-1 px-3">
          <Link className={navItemClass('/dashboard')} href="/dashboard">
            ▦ &nbsp; Overview
          </Link>
          <Link className={navItemClass('/dashboard/subdomains')} href="/dashboard/subdomains">
            ◎ &nbsp; My Subdomains
          </Link>
          <Link className={navItemClass('/dashboard/dns')} href="/dashboard/dns">
            ◇ &nbsp; DNS Records
          </Link>
        </nav>

        <p className="px-4 py-2 pt-6 text-xs font-semibold uppercase tracking-widest text-slate-400">Billing</p>
        <nav className="space-y-1 px-3">
          <Link className={navItemClass('/dashboard/billing')} href="/dashboard/billing">
            $ &nbsp; Wallet
          </Link>
          <Link className={navItemClass('/dashboard/transactions')} href="/dashboard/transactions">
            ↗ &nbsp; Transactions
          </Link>
        </nav>

        <p className="px-4 py-2 pt-6 text-xs font-semibold uppercase tracking-widest text-slate-400">Account</p>
        <nav className="space-y-1 px-3">
          <Link className={navItemClass('/dashboard/settings')} href="/dashboard/settings">
            ⚙ &nbsp; Settings
          </Link>
          <Link className={navItemClass('/dashboard/notifications')} href="/dashboard/notifications">
            ● &nbsp; Notifications
          </Link>
          <Link className={navItemClass('/dashboard/help')} href="/dashboard/help">
            ? &nbsp; Help & Support
          </Link>
          <Link className="block rounded-xl px-3 py-2.5 text-sm text-slate-300 hover:bg-slate-800 hover:text-white" href="/admin">
            ▣ &nbsp; Admin demo
          </Link>
        </nav>

        <div className="mt-auto border-t border-slate-800 p-4">
          <div className="mb-3 flex justify-between rounded-xl border border-slate-800 bg-slate-800 p-3 text-sm">
            <span className="text-slate-300">Wallet balance</span>
            <strong>{balanceDisplay}</strong>
          </div>
          <Link
            href="/dashboard/billing"
            className="mb-4 block rounded-xl bg-indigo-600 px-3 py-2 text-center text-sm font-medium hover:bg-indigo-500"
          >
            Add Credits ＋
          </Link>
          <div className="flex items-center justify-between rounded-xl bg-slate-800 p-3 text-sm">
            <div>
              <strong>{user?.full_name || user?.username || 'User'}</strong>
              <p className="text-xs text-slate-400">{user?.username || 'user'} · Account</p>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="text-xs text-slate-400 hover:text-white"
            >
              Sign out
            </button>
          </div>
          <Link
            href="/"
            className="mt-3 block rounded-xl border border-slate-700 px-3 py-2 text-center text-xs text-slate-300 hover:bg-slate-800"
          >
            Back to public site
          </Link>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        {children}
      </div>
    </div>
  );
}

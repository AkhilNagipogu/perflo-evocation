'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  const navItemClass = (path: string) => {
    const isActive = pathname === path;
    return `block rounded-xl px-3 py-2.5 text-sm transition ${
      isActive
        ? 'bg-indigo-500/20 text-indigo-100 font-semibold'
        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
    }`;
  };

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
          <Link className={navItemClass('/admin')} href="/admin">
            ▣ &nbsp; Admin demo
          </Link>
        </nav>

        <div className="mt-auto border-t border-slate-800 p-4">
          <div className="mb-3 flex justify-between rounded-xl bg-slate-800 p-3 text-sm">
            <span>Wallet balance</span>
            <strong>₹480</strong>
          </div>
          <Link
            href="/dashboard/billing"
            className="block rounded-xl bg-indigo-600 px-3 py-2 text-center text-sm font-medium hover:bg-indigo-500"
          >
            Add Credits ＋
          </Link>
          <p className="mt-4 rounded-xl bg-slate-800 p-3 text-sm">
            Akhil N. <span className="block text-xs text-slate-400">akhil · Account</span>
          </p>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        {children}
      </div>
    </div>
  );
}

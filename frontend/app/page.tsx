'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { searchSubdomain, getParentDomains } from '../lib/api';

export default function HomePage() {
  const [subdomain, setSubdomain] = useState('');
  const [parentDomains, setParentDomains] = useState<any[]>([]);
  const [selectedParentId, setSelectedParentId] = useState('');
  const [selectedDomainName, setSelectedDomainName] = useState('perflo.in');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<any | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDomains() {
      try {
        const domains = await getParentDomains();
        if (domains && domains.length > 0) {
          setParentDomains(domains);
          setSelectedParentId(domains[0].id);
          setSelectedDomainName(domains[0].domain);
        } else {
          setParentDomains([{ id: 'default', domain: 'perflo.in' }]);
          setSelectedDomainName('perflo.in');
        }
      } catch (err) {
        setParentDomains([{ id: 'default', domain: 'perflo.in' }]);
        setSelectedDomainName('perflo.in');
      }
    }
    loadDomains();
  }, []);

  const handleDomainChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setSelectedParentId(id);
    const found = parentDomains.find((d) => d.id === id);
    if (found) setSelectedDomainName(found.domain);
    setSearchResult(null);
    setSearchError(null);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanSubdomain = subdomain.trim().toLowerCase();
    if (!cleanSubdomain || !selectedParentId) return;

    setIsSearching(true);
    setSearchError(null);
    setSearchResult(null);

    try {
      const res = await searchSubdomain(cleanSubdomain, selectedParentId);
      setSearchResult(res);
    } catch (err: any) {
      setSearchError(err.message || 'Error checking subdomain availability');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-4 py-4 md:px-8">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 font-bold text-white">
              P
            </span>
            <span>
              <strong className="block text-lg">Prflo</strong>
              <small className="text-xs uppercase tracking-widest text-slate-500">by Evocation</small>
            </span>
          </Link>
          <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex">
            <a href="#features" className="hover:text-slate-900">Features</a>
            <a href="#how-it-works" className="hover:text-slate-900">How It Works</a>
            <a href="#pricing" className="hover:text-slate-900">Pricing</a>
            <a href="#faq" className="hover:text-slate-900">FAQ</a>
          </nav>
          <div className="flex items-center gap-2">
            <Link href="/login" className="rounded-full px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
              Log In
            </Link>
            <Link href="/register" className="rounded-full bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="mx-auto grid max-w-7xl gap-10 px-4 py-16 md:px-8 lg:grid-cols-[1.1fr_0.9fr] lg:py-24">
          <div className="space-y-8">
            <div className="inline-flex rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-indigo-700">
              ✦ Live SaaS Subdomain Platform
            </div>
            <div className="space-y-5">
              <h1 className="max-w-xl text-4xl font-black tracking-tight text-slate-900 md:text-6xl">
                Your space on the internet.
              </h1>
              <p className="max-w-xl text-lg text-slate-600">
                Get your own subdomain for your portfolio, college project, personal website, or next big idea. Simple pricing, straightforward DNS management, and control over your own subdomain.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
              <form onSubmit={handleSearch} className="flex flex-col gap-3 lg:flex-row">
                <input
                  type="text"
                  value={subdomain}
                  onChange={(e) => setSubdomain(e.target.value.toLowerCase())}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none focus:border-indigo-500"
                  placeholder="Choose your name"
                  aria-label="Subdomain prefix"
                  required
                />
                {parentDomains.length > 1 ? (
                  <select
                    value={selectedParentId}
                    onChange={handleDomainChange}
                    className="rounded-xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-600 outline-none"
                  >
                    {parentDomains.map((d) => (
                      <option key={d.id} value={d.id}>
                        . {d.domain}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className="flex items-center justify-center rounded-xl bg-slate-100 px-4 py-3 text-sm font-medium text-slate-600 whitespace-nowrap">
                    . {selectedDomainName}
                  </span>
                )}
                <button
                  type="submit"
                  disabled={isSearching}
                  className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50 whitespace-nowrap"
                >
                  {isSearching ? 'Checking...' : 'Check Availability'}
                </button>
              </form>

              {searchError && (
                <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-600">
                  {searchError}
                </div>
              )}

              {searchResult && (
                <div className={`mt-3 rounded-xl border p-4 ${
                  searchResult.is_available
                    ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
                    : 'border-amber-200 bg-amber-50 text-amber-900'
                }`}>
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <strong className="text-base">{searchResult.full_domain}</strong>
                        <span className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${
                          searchResult.is_available
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-amber-100 text-amber-800'
                        }`}>
                          {searchResult.is_available ? 'Available' : 'Unavailable'}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-slate-600">
                        {searchResult.is_available
                          ? 'Standard Bundle: ₹60/year for 2 subdomains with automated Cloudflare DNS'
                          : searchResult.message || 'This subdomain is currently reserved or already rented.'}
                      </p>
                    </div>

                    {searchResult.is_available ? (
                      <Link
                        href={`/register?subdomain=${encodeURIComponent(searchResult.subdomain_name)}`}
                        className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 whitespace-nowrap"
                      >
                        Claim Subdomain Now →
                      </Link>
                    ) : (
                      <span className="text-xs font-medium text-slate-500">
                        Try another name
                      </span>
                    )}
                  </div>
                </div>
              )}

              <p className="mt-3 text-sm text-slate-500">Starting at ₹60/year (₹5/month) · No hosting required</p>
            </div>

            <Link
              className="inline-flex rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-indigo-700 shadow-sm hover:bg-slate-50"
              href="/dashboard"
            >
              Explore dashboard preview →
            </Link>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-xl">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest text-slate-400">Live preview</p>
                <h2 className="mt-2 text-xl font-semibold">Subdomain preview</h2>
              </div>
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
                ● Active
              </span>
            </div>
            <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-500">
              <div className="flex justify-between">
                <span>Subdomain</span>
                <strong className="text-slate-700">
                  {subdomain ? `${subdomain}.${selectedDomainName}` : `rahul.${selectedDomainName}`}
                </strong>
              </div>
              <div className="flex justify-between">
                <span>Status</span>
                <strong className="text-emerald-700">Active</strong>
              </div>
              <div className="flex justify-between">
                <span>DNS records</span>
                <strong className="text-slate-700">3</strong>
              </div>
              <div className="flex justify-between">
                <span>Rental</span>
                <strong className="text-slate-700">Standard Bundle (₹60/yr)</strong>
              </div>
            </div>
            <div className="mt-5 rounded-2xl border border-indigo-100 bg-indigo-50 p-4">
              <p className="text-xs uppercase tracking-widest text-indigo-600">Enterprise Cloudflare DNS</p>
              <p className="mt-2 text-sm text-indigo-900">
                Live DNS orchestration via Cloudflare with full support for A, AAAA, CNAME, and TXT records, automated grace-period protection, and instantaneous propagation.
              </p>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="mx-auto max-w-7xl px-4 py-16 md:px-8">
          <div className="text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">How it works</p>
            <h2 className="mt-3 text-3xl font-bold md:text-4xl">Simple steps to claim your address.</h2>
          </div>
          <div className="mt-10 grid gap-6 md:grid-cols-3">
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <span className="text-sm font-semibold text-slate-400">01</span>
              <h3 className="mt-3 text-xl font-semibold">Choose your subdomain</h3>
              <p className="mt-3 text-slate-600">Find a name that suits your identity and confirm it is available.</p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <span className="text-sm font-semibold text-slate-400">02</span>
              <h3 className="mt-3 text-xl font-semibold">Add credits and activate</h3>
              <p className="mt-3 text-slate-600">Top up your prepaid wallet and pay the ₹60 yearly rental with instant credits.</p>
            </article>
            <article className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <span className="text-sm font-semibold text-slate-400">03</span>
              <h3 className="mt-3 text-xl font-semibold">Manage DNS and connect</h3>
              <p className="mt-3 text-slate-600">Add DNS records and route your project to Vercel, Netlify, GitHub Pages, or a custom server.</p>
            </article>
          </div>
        </section>

        <section id="features" className="bg-slate-900 py-16 text-white">
          <div className="mx-auto max-w-7xl px-4 md:px-8">
            <p className="text-center text-sm font-semibold uppercase tracking-widest text-indigo-300">Features</p>
            <h2 className="mx-auto mt-3 max-w-3xl text-center text-3xl font-bold md:text-4xl">
              A clean, developer-friendly way to manage your online identity.
            </h2>
            <div className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
              <article className="rounded-2xl border border-slate-700 bg-slate-800 p-6">
                <h3 className="text-xl font-semibold">Your Own Subdomain</h3>
                <p className="mt-3 text-slate-300">Use a memorable subdomain for your portfolio, project or community.</p>
              </article>
              <article className="rounded-2xl border border-slate-700 bg-slate-800 p-6">
                <h3 className="text-xl font-semibold">Simple DNS Management</h3>
                <p className="mt-3 text-slate-300">Set records without the usual friction, propagation delays, or jargon.</p>
              </article>
              <article className="rounded-2xl border border-slate-700 bg-slate-800 p-6">
                <h3 className="text-xl font-semibold">Wallet-Based Payments</h3>
                <p className="mt-3 text-slate-300">Add prepaid credits and pay rental charges directly from your wallet with zero hassle.</p>
              </article>
              <article className="rounded-2xl border border-slate-700 bg-slate-800 p-6">
                <h3 className="text-xl font-semibold">Built for Students & Devs</h3>
                <p className="mt-3 text-slate-300">Ideal for experiments, portfolios, hackathon projects, and side startups.</p>
              </article>
            </div>
          </div>
        </section>

        <section id="pricing" className="mx-auto max-w-7xl px-4 py-16 md:px-8">
          <div className="text-center">
            <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">Pricing</p>
            <h2 className="mt-3 text-3xl font-bold">Simple rental pricing with no hosting bundle.</h2>
          </div>
          <div className="mx-auto mt-10 max-w-xl rounded-3xl border border-indigo-200 bg-white p-8 text-center shadow-lg">
            <div className="text-5xl font-black">₹60</div>
            <div className="mt-2 text-sm uppercase tracking-widest text-slate-500">/ 365 days (2 Subdomains)</div>
            <ul className="mt-8 space-y-3 text-left text-slate-600">
              <li>✓ <strong>2 active subdomains</strong> included in base plan.</li>
              <li>✓ Real Cloudflare DNS management through the dashboard.</li>
              <li>✓ Prepaid wallet-based rental payments.</li>
              <li>✓ 5-day grace period protection upon expiration.</li>
              <li>✓ Subdomain rename capability with cooldown protection.</li>
              <li>✓ Connect freely to external hosting (GitHub Pages, Vercel, VPS).</li>
            </ul>
            <Link
              href="/register"
              className="mt-8 block rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white hover:bg-indigo-500"
            >
              Get Started with ₹60 Plan
            </Link>
          </div>
        </section>

        <section id="faq" className="bg-slate-100 py-16">
          <div className="mx-auto max-w-5xl px-4 md:px-8">
            <div className="text-center">
              <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">FAQ</p>
              <h2 className="mt-3 text-3xl font-bold">Questions people usually ask.</h2>
            </div>
            <div className="mt-10 space-y-4">
              <article className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-lg font-semibold">What is a subdomain?</h3>
                <p className="mt-3 text-slate-600">A custom hostname attached to a parent domain, such as project.perflo.in.</p>
              </article>
              <article className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-lg font-semibold">Do I get website hosting?</h3>
                <p className="mt-3 text-slate-600">No. Evocation focuses on subdomain rental and DNS orchestration. You connect your subdomain to external services like Vercel, Netlify, Render, or a VPS.</p>
              </article>
              <article className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-lg font-semibold">Can I manage DNS records?</h3>
                <p className="mt-3 text-slate-600">Yes. The dashboard includes a complete DNS editor for A, AAAA, CNAME, and TXT records with optional Cloudflare proxying.</p>
              </article>
              <article className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-lg font-semibold">How do wallet credits work?</h3>
                <p className="mt-3 text-slate-600">You add prepaid funds (minimum ₹60 first funding) to your wallet, and subscription renewals are safely debited automatically.</p>
              </article>
              <article className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-lg font-semibold">What happens when my rental expires?</h3>
                <p className="mt-3 text-slate-600">You enter a strict 5-day (120-hour) grace period. DNS remains active so your site stays up while you reactivate. If not renewed, records are released.</p>
              </article>
              <article className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-lg font-semibold">Can I change my subdomain?</h3>
                <p className="mt-3 text-slate-600">Yes, you can rename your subdomain to any available name while preserving your original expiration date, protected by a 24-hour rename cooldown.</p>
              </article>
              <article className="rounded-2xl border border-slate-200 bg-white p-5">
                <h3 className="text-lg font-semibold">What happens when my wallet runs out?</h3>
                <p className="mt-3 text-slate-600">You can top up your wallet anytime from the billing tab using secure payments or demo credits.</p>
              </article>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white px-4 py-8 text-center text-sm text-slate-600">
        <p>Prflo by Evocation — a simple platform for renting and managing subdomains.</p>
        <p className="mt-3">
          <Link href="/login" className="text-indigo-600 hover:underline">Sign in</Link> ·{' '}
          <Link href="/dashboard" className="text-indigo-600 hover:underline">Dashboard</Link> ·{' '}
          <Link href="/dashboard/help" className="text-indigo-600 hover:underline">Help & Support</Link> ·{' '}
          <Link href="/abuse" className="text-indigo-600 hover:underline">Report Abuse</Link>
        </p>
      </footer>
    </>
  );
}

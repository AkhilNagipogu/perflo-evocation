'use client';

import { useState } from 'react';

export default function HelpSupportPage() {
  const [aiQuery, setAiQuery] = useState('');
  const [aiAnswer, setAiAnswer] = useState<string | null>(null);
  const [contactSubject, setContactSubject] = useState('');
  const [contactCategory, setContactCategory] = useState('Billing');
  const [contactMessage, setContactMessage] = useState('');
  const [contactSubmitted, setContactSubmitted] = useState(false);

  const handleAskAI = (e: React.FormEvent) => {
    e.preventDefault();
    if (!aiQuery.trim()) return;

    const q = aiQuery.toLowerCase();
    if (q.includes('dns') || q.includes('record') || q.includes('a record') || q.includes('cname')) {
      setAiAnswer(
        'To configure DNS: Go to DNS Records in the sidebar, select your active subdomain, and click "Add Record". A records point to IPv4 server addresses, and CNAME records alias your subdomain to platforms like GitHub Pages, Vercel, or Render.'
      );
    } else if (q.includes('wallet') || q.includes('credit') || q.includes('cost') || q.includes('price')) {
      setAiAnswer(
        'Prflo uses a prepaid wallet system in Indian Rupees (INR). Subdomains are rented at ₹60/year for a 2-domain bundle. You can add credits in multiples of ₹10, ₹50, or ₹100 via the Wallet section.'
      );
    } else if (q.includes('renew') || q.includes('expir') || q.includes('grace')) {
      setAiAnswer(
        'Rentals expire at the end of their 365-day period. There is an automatic 5-day grace period during which DNS remains active. Enable auto-renew on your Subdomains page to let your wallet automatically renew them before expiration.'
      );
    } else {
      setAiAnswer(
        `Regarding "${aiQuery}": Prflo by Evocation provides fast, instant Cloudflare-synced subdomain rentals. You can manage DNS records directly from your dashboard and renew or rename subdomains anytime.`
      );
    }
  };

  const handleContactSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!contactMessage.trim()) return;
    setContactSubmitted(true);
    setContactSubject('');
    setContactMessage('');
    setTimeout(() => setContactSubmitted(false), 4000);
  };

  return (
    <>
      <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-8">
        <p className="text-sm uppercase tracking-widest text-slate-400">Dashboard</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">Help &amp; Support</h1>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        {/* AI Assistant Section */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 font-semibold text-indigo-600">
            <span>▤</span> &nbsp; Demo AI assistant
          </div>
          <form onSubmit={handleAskAI} className="mt-4 flex flex-col gap-3 md:flex-row">
            <input
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
              placeholder="Ask about subdomains, DNS or wallet credits"
              value={aiQuery}
              onChange={(e) => setAiQuery(e.target.value)}
            />
            <button
              type="submit"
              className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500 whitespace-nowrap"
            >
              Ask
            </button>
          </form>

          {aiAnswer ? (
            <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50/70 p-4 text-sm text-slate-800">
              <strong className="block mb-1 text-indigo-900">Assistant Response:</strong>
              {aiAnswer}
            </div>
          ) : (
            <p className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
              This demo assistant can answer common questions about subdomains, DNS records, wallet credits, and rental expiry.
            </p>
          )}
        </section>

        {/* 2-Column Contact and Email section */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Contact Support */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Contact support</h2>

            {contactSubmitted && (
              <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
                Your support message has been submitted. Our team will review it shortly.
              </div>
            )}

            <form onSubmit={handleContactSubmit} className="mt-4 space-y-3">
              <input
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                placeholder="Subject"
                required
                value={contactSubject}
                onChange={(e) => setContactSubject(e.target.value)}
              />
              <select
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-800 focus:outline-none"
                value={contactCategory}
                onChange={(e) => setContactCategory(e.target.value)}
              >
                <option>Billing</option>
                <option>DNS</option>
                <option>Account</option>
                <option>General</option>
              </select>
              <textarea
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
                placeholder="Message"
                rows={5}
                required
                value={contactMessage}
                onChange={(e) => setContactMessage(e.target.value)}
              />
              <button
                type="submit"
                className="mt-4 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                Submit
              </button>
            </form>
          </section>

          {/* Email Us & FAQ Links */}
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">Email us</h2>
            <p className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
              support@demo.prflo.example — demo placeholder email only
            </p>
            <div className="mt-6 space-y-3">
              <div
                onClick={() => {
                  setAiQuery('How do I configure an A record?');
                  setAiAnswer(
                    'An A record maps your hostname to an IPv4 address (e.g. 192.0.2.1). Enter @ for the root of your subdomain or a host prefix, enter your server IP in the content field, choose a TTL (usually 300s), and click save.'
                  );
                }}
                className="cursor-pointer flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-800 hover:bg-indigo-50 hover:border-indigo-200 transition"
              >
                <span>How do I configure an A record?</span>
                <span className="text-slate-400">›</span>
              </div>
              <div
                onClick={() => {
                  setAiQuery('How do I connect an external website?');
                  setAiAnswer(
                    'To connect an external website on Vercel, Netlify, or GitHub Pages: Add a CNAME record pointing to your provider host (e.g. cname.vercel-dns.com) or an A record pointing to their load balancer IP.'
                  );
                }}
                className="cursor-pointer flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-800 hover:bg-indigo-50 hover:border-indigo-200 transition"
              >
                <span>How do I connect an external website?</span>
                <span className="text-slate-400">›</span>
              </div>
              <div
                onClick={() => {
                  setAiQuery('What happens when my rental expires?');
                  setAiAnswer(
                    'When a rental expires, you enter a 5-day grace period. DNS remains active. If not renewed by the 5th day, the subdomain enters a 30-day quarantine and DNS records are deleted before becoming available for registration again.'
                  );
                }}
                className="cursor-pointer flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-800 hover:bg-indigo-50 hover:border-indigo-200 transition"
              >
                <span>What happens when my rental expires?</span>
                <span className="text-slate-400">›</span>
              </div>
            </div>
          </section>
        </div>
      </main>
    </>
  );
}

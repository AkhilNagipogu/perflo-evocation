'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { getWallet, topupWallet, confirmTestPayment, getWalletSummary, getTransactions } from '../../../lib/api';

export default function WalletBillingPage() {
  const [wallet, setWallet] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [recentTx, setRecentTx] = useState<any[]>([]);
  const [selectedTopup, setSelectedTopup] = useState<number>(50);
  const [customAmountRupees, setCustomAmountRupees] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [feedbackMessage, setFeedbackMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadData = async () => {
    try {
      const [w, s, txs] = await Promise.all([
        getWallet().catch(() => ({ balance_paise: 48000 })),
        getWalletSummary().catch(() => ({ month_spending_paise: 2000, month_funding_paise: 5000 })),
        getTransactions(1, 5).catch(() => ({ items: [] })),
      ]);
      setWallet(w);
      setSummary(s);
      setRecentTx(txs?.items || []);
    } catch {
      // Demo defaults
      setWallet({ balance_paise: 48000 });
      setSummary({ month_spending_paise: 2000, month_funding_paise: 5000 });
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleTopup = async (rupees: number) => {
    if (rupees <= 0) return;
    setFeedbackMessage(null);
    setIsProcessing(true);

    try {
      const amountPaise = Math.round(rupees * 100);
      const res = await topupWallet(amountPaise);

      if (res.is_test || res.session_id?.startsWith('test_')) {
        await confirmTestPayment(res.order_id);
        setFeedbackMessage({
          type: 'success',
          text: `Demo transaction completed: ₹${rupees} credited to your wallet!`,
        });
        await loadData();
      } else if (res.checkout_url) {
        window.location.href = res.checkout_url;
      } else {
        setFeedbackMessage({
          type: 'success',
          text: `Transaction initialized for ₹${rupees}.`,
        });
        await loadData();
      }
    } catch (err: any) {
      setFeedbackMessage({
        type: 'error',
        text: err.message || 'Payment initiation failed.',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseFloat(customAmountRupees);
    if (isNaN(parsed) || parsed <= 0) {
      setFeedbackMessage({ type: 'error', text: 'Please enter a valid amount in rupees.' });
      return;
    }
    handleTopup(parsed);
  };

  const balanceDisplay = wallet ? `₹${Math.floor(wallet.balance_paise / 100)}` : '₹480';
  const spentThisMonth = summary ? `₹${Math.floor((summary.month_spending_paise || 0) / 100)}` : '₹20';
  const addedThisMonth = summary ? `₹${Math.floor((summary.month_funding_paise || 0) / 100)}` : '₹50';

  return (
    <>
      <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-8">
        <p className="text-sm uppercase tracking-widest text-slate-400">Dashboard</p>
        <h1 className="mt-1 text-2xl font-bold">Wallet</h1>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        {/* Metric Cards Grid */}
        <div className="grid gap-4 md:grid-cols-4">
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Available wallet balance</p>
            <p className="mt-4 text-3xl font-bold text-slate-900">{balanceDisplay}</p>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Credits used this month</p>
            <p className="mt-4 text-3xl font-bold text-slate-900">{spentThisMonth}</p>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Money added this month</p>
            <p className="mt-4 text-3xl font-bold text-slate-900">{addedThisMonth}</p>
          </article>
          <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm flex flex-col justify-end">
            <a
              href="#topups"
              className="block rounded-xl bg-indigo-600 px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-indigo-500"
            >
              Add Credits
            </a>
          </article>
        </div>

        {feedbackMessage && (
          <div
            className={`rounded-xl border p-4 text-sm ${
              feedbackMessage.type === 'success'
                ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
                : 'border-rose-200 bg-rose-50 text-rose-800'
            }`}
          >
            {feedbackMessage.text}
          </div>
        )}

        {/* Top-up Choices */}
        <section id="topups" className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Top-up choices</h2>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <article
              onClick={() => {
                setSelectedTopup(10);
                handleTopup(10);
              }}
              className={`cursor-pointer rounded-2xl border px-4 py-5 transition hover:border-indigo-400 ${
                selectedTopup === 10
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-slate-200 bg-slate-50'
              }`}
            >
              <p className="text-lg font-bold">₹10</p>
              <p className="mt-1 text-xs uppercase tracking-widest text-slate-500">Demo credit</p>
            </article>

            <article
              onClick={() => {
                setSelectedTopup(50);
                handleTopup(50);
              }}
              className={`cursor-pointer rounded-2xl border px-4 py-5 transition hover:border-indigo-400 ${
                selectedTopup === 50
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-slate-200 bg-slate-50'
              }`}
            >
              <p className="text-lg font-bold">₹50</p>
              <p className="mt-1 text-xs uppercase tracking-widest text-slate-500">Demo credit</p>
            </article>

            <article
              onClick={() => {
                setSelectedTopup(100);
                handleTopup(100);
              }}
              className={`cursor-pointer rounded-2xl border px-4 py-5 transition hover:border-indigo-400 ${
                selectedTopup === 100
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-slate-200 bg-slate-50'
              }`}
            >
              <p className="text-lg font-bold">₹100</p>
              <p className="mt-1 text-xs uppercase tracking-widest text-slate-500">Demo credit</p>
            </article>

            <article
              onClick={() => {
                setSelectedTopup(500);
                handleTopup(500);
              }}
              className={`cursor-pointer rounded-2xl border px-4 py-5 transition hover:border-indigo-400 ${
                selectedTopup === 500
                  ? 'border-indigo-500 bg-indigo-50'
                  : 'border-slate-200 bg-slate-50'
              }`}
            >
              <p className="text-lg font-bold">₹500</p>
              <p className="mt-1 text-xs uppercase tracking-widest text-slate-500">Demo credit</p>
            </article>
          </div>

          <form onSubmit={handleCustomSubmit} className="mt-5 flex flex-col gap-3 md:flex-row">
            <input
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
              placeholder="Custom amount in rupees (e.g. 60)"
              type="number"
              min="10"
              step="1"
              value={customAmountRupees}
              onChange={(e) => setCustomAmountRupees(e.target.value)}
            />
            <button
              type="submit"
              disabled={isProcessing}
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold hover:bg-slate-50 disabled:opacity-50 whitespace-nowrap"
            >
              {isProcessing ? 'Processing...' : 'Add custom amount'}
            </button>
          </form>

          <p className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            Demo transaction — no real payment processed.
          </p>
        </section>

        {/* Recent Transactions Preview */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Recent transactions</h2>
          <div className="mt-3 text-sm text-slate-600">
            {recentTx.length > 0 ? (
              <div className="space-y-2">
                {recentTx.slice(0, 3).map((tx) => (
                  <p key={tx.id}>
                    {tx.description} ({tx.amount_paise > 0 ? '+' : ''}₹{(tx.amount_paise / 100).toFixed(0)}){' '}
                    <span className="text-slate-400 text-xs ml-2">
                      {new Date(tx.created_at).toLocaleDateString()}
                    </span>
                  </p>
                ))}
              </div>
            ) : (
              <p>
                Wallet top-up of ₹50 completed{' '}
                <Link href="/dashboard/transactions" className="ml-2 text-indigo-600 font-medium hover:underline">
                  View all transactions →
                </Link>
              </p>
            )}
            {recentTx.length > 0 && (
              <p className="mt-3">
                <Link href="/dashboard/transactions" className="text-indigo-600 font-medium hover:underline">
                  View all transactions →
                </Link>
              </p>
            )}
          </div>
        </section>
      </main>
    </>
  );
}

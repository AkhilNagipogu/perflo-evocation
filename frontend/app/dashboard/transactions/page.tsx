'use client';

import { useState, useEffect } from 'react';
import { getTransactions } from '../../../lib/api';

interface Transaction {
  id: string;
  reference_id: string;
  transaction_type: string;
  description: string;
  amount_paise: number;
  balance_after_paise: number;
  status?: string;
  created_at: string;
}

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('All types');
  const [statusFilter, setStatusFilter] = useState('All statuses');
  const [isLoading, setIsLoading] = useState(true);

  const defaultDemoTransactions: Transaction[] = [
    {
      id: 'tx-1',
      reference_id: 'WT-1001',
      transaction_type: 'topup',
      description: 'Demo wallet top-up',
      amount_paise: 5000,
      balance_after_paise: 5000,
      status: 'completed',
      created_at: '14 Oct 2026',
    },
    {
      id: 'tx-2',
      reference_id: 'REN-1002',
      transaction_type: 'rental',
      description: 'Rental charge for rahul.evocation.in',
      amount_paise: -1000,
      balance_after_paise: 4000,
      status: 'completed',
      created_at: '21 Oct 2026',
    },
    {
      id: 'tx-3',
      reference_id: 'REN-1003',
      transaction_type: 'rental',
      description: 'Rental charge for project.evocation.in',
      amount_paise: -1000,
      balance_after_paise: 3000,
      status: 'completed',
      created_at: '18 Oct 2026',
    },
  ];

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getTransactions(1, 50);
        if (data && data.items && data.items.length > 0) {
          setTransactions(data.items);
        } else {
          setTransactions(defaultDemoTransactions);
        }
      } catch {
        setTransactions(defaultDemoTransactions);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, []);

  const filtered = transactions.filter((tx) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      tx.reference_id?.toLowerCase().includes(q) ||
      tx.description?.toLowerCase().includes(q) ||
      tx.transaction_type?.toLowerCase().includes(q);

    let matchesType = true;
    if (typeFilter === 'Top-up') {
      matchesType = tx.transaction_type.toLowerCase().includes('topup') || tx.transaction_type.toLowerCase().includes('credit');
    } else if (typeFilter === 'Rental') {
      matchesType = tx.transaction_type.toLowerCase().includes('rental') || tx.transaction_type.toLowerCase().includes('debit');
    }

    let matchesStatus = true;
    const currentStatus = (tx.status || 'completed').toLowerCase();
    if (statusFilter !== 'All statuses') {
      matchesStatus = currentStatus === statusFilter.toLowerCase();
    }

    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <>
      <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-8">
        <p className="text-sm uppercase tracking-widest text-slate-400">Dashboard</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">Transactions</h1>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        {/* Search & Filter Bar */}
        <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row">
          <input
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none"
            placeholder="Search transactions"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <select
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 focus:outline-none"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option>All types</option>
            <option>Top-up</option>
            <option>Rental</option>
          </select>
          <select
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 focus:outline-none"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option>All statuses</option>
            <option>Completed</option>
            <option>Pending</option>
            <option>Failed</option>
          </select>
        </section>

        {/* Transactions Table Card */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-5 py-3">Date</th>
                  <th className="px-5 py-3">Transaction ID</th>
                  <th className="px-5 py-3">Type</th>
                  <th className="px-5 py-3">Description</th>
                  <th className="px-5 py-3">Amount</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-5 py-8 text-center text-slate-500">
                      No transactions matched the criteria.
                    </td>
                  </tr>
                ) : (
                  filtered.map((tx) => {
                    const isCredit = tx.amount_paise > 0;
                    const dateDisplay =
                      typeof tx.created_at === 'string' && tx.created_at.includes('T')
                        ? new Date(tx.created_at).toLocaleDateString('en-GB', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                          })
                        : tx.created_at;

                    return (
                      <tr key={tx.id} className="border-t border-slate-200 hover:bg-slate-50/50">
                        <td className="px-5 py-4 text-slate-700">{dateDisplay}</td>
                        <td className="px-5 py-4 font-mono font-medium text-slate-900">{tx.reference_id}</td>
                        <td className="px-5 py-4 uppercase text-slate-700 text-xs font-semibold">{tx.transaction_type}</td>
                        <td className="px-5 py-4 text-slate-800">{tx.description}</td>
                        <td
                          className={`px-5 py-4 font-semibold ${
                            isCredit ? 'text-emerald-600' : 'text-slate-900'
                          }`}
                        >
                          {isCredit ? '+' : ''}₹{Math.abs(Math.floor(tx.amount_paise / 100))}
                        </td>
                        <td className="px-5 py-4">
                          <span className="inline-block rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                            {tx.status || 'completed'}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </>
  );
}

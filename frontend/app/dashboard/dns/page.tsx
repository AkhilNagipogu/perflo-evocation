'use client';

import { useState, useEffect } from 'react';
import { getMyRentals, getDnsRecords, createDnsRecord, deleteDnsRecord } from '../../../lib/api';

interface DnsRecord {
  id: string;
  record_type: string;
  name?: string;
  content: string;
  ttl: number;
  proxied: boolean;
  updated_at?: string;
  created_at?: string;
}

export default function DnsRecordsPage() {
  const [rentals, setRentals] = useState<any[]>([]);
  const [selectedRentalId, setSelectedRentalId] = useState<string>('');
  const [selectedSubdomainName, setSelectedSubdomainName] = useState<string>('rahul.evocation.in');
  const [records, setRecords] = useState<DnsRecord[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('All types');
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // New Record Form State
  const [newType, setNewType] = useState('A');
  const [newName, setNewName] = useState('@');
  const [newContent, setNewContent] = useState('');
  const [newTtl, setNewTtl] = useState(300);
  const [newProxied, setNewProxied] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fallback demo records if empty
  const defaultDemoRecords: DnsRecord[] = [
    {
      id: 'rec-1',
      record_type: 'A',
      name: '@',
      content: '34.120.57.90',
      ttl: 300,
      proxied: false,
      updated_at: '19 Oct 2026',
    },
    {
      id: 'rec-2',
      record_type: 'CNAME',
      name: 'www',
      content: 'rahul.evocation.in',
      ttl: 600,
      proxied: false,
      updated_at: '21 Oct 2026',
    },
  ];

  useEffect(() => {
    async function init() {
      try {
        const myRentals = await getMyRentals();
        if (myRentals && myRentals.length > 0) {
          setRentals(myRentals);
          setSelectedRentalId(myRentals[0].id);
          setSelectedSubdomainName(myRentals[0].full_domain);
          await loadRecords(myRentals[0].id);
        } else {
          // Demo fallback
          setRentals([
            { id: 'demo-1', full_domain: 'rahul.evocation.in' },
            { id: 'demo-2', full_domain: 'project.evocation.in' },
          ]);
          setSelectedSubdomainName('rahul.evocation.in');
          setRecords(defaultDemoRecords);
        }
      } catch (err) {
        // Fallback for mock mode
        setRentals([
          { id: 'demo-1', full_domain: 'rahul.evocation.in' },
          { id: 'demo-2', full_domain: 'project.evocation.in' },
        ]);
        setSelectedSubdomainName('rahul.evocation.in');
        setRecords(defaultDemoRecords);
      } finally {
        setIsLoading(false);
      }
    }
    init();
  }, []);

  const loadRecords = async (rentalId: string) => {
    try {
      const data = await getDnsRecords(rentalId);
      if (data && data.length > 0) {
        setRecords(data);
      } else {
        setRecords(defaultDemoRecords);
      }
    } catch {
      setRecords(defaultDemoRecords);
    }
  };

  const handleSubdomainChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    const found = rentals.find((r) => r.id === val || r.full_domain === val);
    if (found) {
      setSelectedRentalId(found.id);
      setSelectedSubdomainName(found.full_domain);
      loadRecords(found.id);
    } else {
      setSelectedSubdomainName(val);
    }
  };

  const handleAddRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!newContent) {
      setFormError('Record content is required.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (selectedRentalId && !selectedRentalId.startsWith('demo-')) {
        await createDnsRecord(selectedRentalId, {
          record_type: newType,
          content: newContent,
          ttl: Number(newTtl),
          proxied: newProxied,
        });
        await loadRecords(selectedRentalId);
      } else {
        // Local simulation
        const newRec: DnsRecord = {
          id: `rec-${Date.now()}`,
          record_type: newType,
          name: newName || '@',
          content: newContent,
          ttl: Number(newTtl),
          proxied: newProxied,
          updated_at: 'Just now',
        };
        setRecords([newRec, ...records]);
      }
      setIsModalOpen(false);
      setNewContent('');
    } catch (err: any) {
      setFormError(err.message || 'Failed to create record.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteRecord = async (recId: string) => {
    if (!confirm('Are you sure you want to delete this DNS record?')) return;
    try {
      if (selectedRentalId && !selectedRentalId.startsWith('demo-')) {
        await deleteDnsRecord(recId);
        await loadRecords(selectedRentalId);
      } else {
        setRecords(records.filter((r) => r.id !== recId));
      }
    } catch {
      setRecords(records.filter((r) => r.id !== recId));
    }
  };

  const filteredRecords = records.filter((r) => {
    const matchesSearch =
      r.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.name && r.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      r.record_type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === 'All types' || r.record_type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <>
      <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-8">
        <p className="text-sm uppercase tracking-widest text-slate-400">Dashboard</p>
        <h1 className="mt-1 text-2xl font-bold">DNS Records</h1>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        {/* Controls Card */}
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-sm uppercase tracking-widest text-slate-400">DNS Records</p>
              <h2 className="text-2xl font-bold">{selectedSubdomainName}</h2>
            </div>
            <div className="flex gap-2">
              <select
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 focus:outline-none"
                value={selectedRentalId || selectedSubdomainName}
                onChange={handleSubdomainChange}
              >
                {rentals.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.full_domain}
                  </option>
                ))}
              </select>
              <button
                onClick={() => setIsModalOpen(true)}
                className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500"
              >
                Add Record
              </button>
            </div>
          </div>

          <div className="mt-5 flex gap-3">
            <input
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm focus:border-indigo-500 focus:bg-white focus:outline-none"
              placeholder="Search records"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <select
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm focus:outline-none"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option>All types</option>
              <option>A</option>
              <option>AAAA</option>
              <option>CNAME</option>
              <option>TXT</option>
            </select>
          </div>
        </section>

        {/* DNS Table Card */}
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-5 py-3">Type</th>
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Content</th>
                  <th className="px-5 py-3">TTL</th>
                  <th className="px-5 py-3">Proxy</th>
                  <th className="px-5 py-3">Last modified</th>
                  <th className="px-5 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-5 py-8 text-center text-slate-500">
                      No DNS records found. Click &quot;Add Record&quot; to create one.
                    </td>
                  </tr>
                ) : (
                  filteredRecords.map((rec) => (
                    <tr key={rec.id} className="border-t border-slate-200 hover:bg-slate-50/50">
                      <td className="px-5 py-4 font-medium text-slate-900">{rec.record_type}</td>
                      <td className="px-5 py-4 text-slate-700">{rec.name || '@'}</td>
                      <td className="px-5 py-4 font-mono text-xs text-slate-600">{rec.content}</td>
                      <td className="px-5 py-4 text-slate-600">{rec.ttl}</td>
                      <td className="px-5 py-4">
                        <span
                          className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${
                            rec.proxied
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {rec.proxied ? 'Proxied' : 'Disabled'}
                        </span>
                      </td>
                      <td className="px-5 py-4 text-slate-600">
                        {rec.updated_at
                          ? typeof rec.updated_at === 'string' && rec.updated_at.includes('T')
                            ? new Date(rec.updated_at).toLocaleDateString()
                            : rec.updated_at
                          : '19 Oct 2026'}
                      </td>
                      <td className="space-x-3 px-5 py-4">
                        <button
                          onClick={() => {
                            setNewType(rec.record_type);
                            setNewContent(rec.content);
                            setNewTtl(rec.ttl);
                            setNewProxied(rec.proxied);
                            setIsModalOpen(true);
                          }}
                          className="font-medium text-indigo-600 hover:underline"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteRecord(rec.id)}
                          className="font-medium text-rose-600 hover:underline"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Prototype banner */}
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          DNS changes in this prototype are simulated and do not modify live DNS records.
        </p>
      </main>

      {/* Add Record Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">Add DNS Record</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
                {formError}
              </div>
            )}

            <form onSubmit={handleAddRecord} className="mt-4 space-y-4 text-sm">
              <div>
                <label className="block font-medium text-slate-700">Type</label>
                <select
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-800"
                  value={newType}
                  onChange={(e) => setNewType(e.target.value)}
                >
                  <option value="A">A (IPv4)</option>
                  <option value="AAAA">AAAA (IPv6)</option>
                  <option value="CNAME">CNAME (Alias)</option>
                  <option value="TXT">TXT (Verification / SPF)</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-700">Name</label>
                <input
                  type="text"
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-800 font-mono"
                  placeholder="@ or subdomain"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700">Content / Target</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-800 font-mono"
                  placeholder={newType === 'A' ? '192.0.2.1' : newType === 'CNAME' ? 'target.domain.com' : 'v=spf1 ...'}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-slate-700">TTL (seconds)</label>
                  <select
                    className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-800"
                    value={newTtl}
                    onChange={(e) => setNewTtl(Number(e.target.value))}
                  >
                    <option value={300}>300 (5 min)</option>
                    <option value={600}>600 (10 min)</option>
                    <option value={1800}>1800 (30 min)</option>
                    <option value={3600}>3600 (1 hour)</option>
                    <option value={86400}>86400 (1 day)</option>
                  </select>
                </div>
                <div>
                  <label className="block font-medium text-slate-700">Proxy Status</label>
                  <label className="mt-2.5 flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newProxied}
                      onChange={(e) => setNewProxied(e.target.checked)}
                      className="rounded border-slate-300 text-indigo-600"
                    />
                    <span className="text-xs text-slate-600 font-medium">Cloudflare proxy</span>
                  </label>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-xl border border-slate-200 px-4 py-2 font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-xl bg-indigo-600 px-4 py-2 font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : 'Save Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

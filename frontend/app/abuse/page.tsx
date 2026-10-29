'use client';

import { useState } from 'react';
import Link from 'next/link';
import { submitAbuseReport } from '../../lib/api';

export default function AbuseReportPage() {
  const [domain, setDomain] = useState('');
  const [category, setCategory] = useState('phishing');
  const [description, setDescription] = useState('');
  const [reporterEmail, setReporterEmail] = useState('');
  const [reporterName, setReporterName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [referenceId, setReferenceId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setReferenceId(null);

    try {
      const res = await submitAbuseReport({
        reported_domain: domain.trim(),
        category,
        description: description.trim(),
        reporter_email: reporterEmail.trim() || undefined,
        reporter_name: reporterName.trim() || undefined,
      });
      setReferenceId(res.reference_id);
    } catch (err: any) {
      setError(err.message || 'Failed to submit report. Please check the inputs.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 font-bold text-white">
              P
            </span>
            <span>
              <strong className="block text-xl text-slate-900">Prflo</strong>
              <small className="text-[10px] uppercase tracking-widest text-slate-500">by Evocation</small>
            </span>
          </Link>
          <Link href="/" className="text-sm font-medium text-slate-600 hover:text-slate-900">
            Back to Home
          </Link>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <h1 className="text-2xl font-bold text-slate-900">
            Report Subdomain Abuse
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            We maintain zero tolerance for malware, phishing, scam networks, and illegal material. All reports are immediately reviewed.
          </p>

          {referenceId ? (
            <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 p-6 text-center">
              <div className="text-4xl mb-3">🛡️</div>
              <h2 className="text-lg font-bold text-emerald-800">
                Report Received
              </h2>
              <p className="mt-2 text-sm text-slate-600">
                Your abuse tracking reference code is:
              </p>
              <div className="mt-3 inline-block rounded-xl border border-emerald-300 bg-white px-4 py-2 font-mono font-bold text-emerald-900 text-lg shadow-sm">
                {referenceId}
              </div>
              <p className="mt-4 text-xs text-slate-500">
                Save this reference number to inquire about the status of this case.
              </p>
              <div className="mt-6">
                <Link
                  href="/"
                  className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500"
                >
                  Return to Home
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {error && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700">Reported Subdomain</label>
                <input
                  type="text"
                  required
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none text-sm"
                  placeholder="badsubdomain.perflo.in"
                  value={domain}
                  onChange={(e) => setDomain(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">Abuse Category</label>
                <select
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-800 focus:outline-none text-sm"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  <option value="phishing">Phishing / Credential Harvesting</option>
                  <option value="malware">Malware / Ransomware Distribution</option>
                  <option value="impersonation">Brand Impersonation / Fraud</option>
                  <option value="spam">Unsolicited Bulk Messaging (Spam)</option>
                  <option value="illegal_content">Illegal or Prohibited Content</option>
                  <option value="trademark">Trademark or Copyright Infringement</option>
                  <option value="other">Other Violation</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700">Detailed Description of Incident</label>
                <textarea
                  required
                  rows={4}
                  className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none text-sm"
                  placeholder="Please describe why this domain constitutes abuse, steps to reproduce, or relevant context (min 20 characters)..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700">Your Email (optional)</label>
                  <input
                    type="email"
                    className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none text-sm"
                    placeholder="contact@domain.com"
                    value={reporterEmail}
                    onChange={(e) => setReporterEmail(e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700">Your Name (optional)</label>
                  <input
                    type="text"
                    className="mt-1 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-slate-900 focus:border-indigo-500 focus:bg-white focus:outline-none text-sm"
                    placeholder="Reporter Name"
                    value={reporterName}
                    onChange={(e) => setReporterName(e.target.value)}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="mt-2 block w-full rounded-xl bg-indigo-600 px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:opacity-50"
              >
                {isLoading ? 'Submitting Report...' : 'Submit Abuse Report'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

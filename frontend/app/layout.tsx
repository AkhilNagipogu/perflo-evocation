import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Prflo — Your space on the internet by Evocation',
  description: 'Get your own subdomain for your portfolio, college project, personal website, or next big idea. Simple pricing, straightforward DNS management, and control over your own subdomain.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}

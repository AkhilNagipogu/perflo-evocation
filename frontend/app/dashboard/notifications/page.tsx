'use client';

import { useState, useEffect } from 'react';
import { getNotifications, markNotificationRead } from '../../../lib/api';

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  category: string;
  is_read: boolean;
  time_ago: string;
}

export default function NotificationsPage() {
  const [filterCategory, setFilterCategory] = useState('All');
  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: 'notif-1',
      title: 'Rental expiring soon',
      message: 'Your project.evocation.in rental expires in 10 days.',
      category: 'rental',
      is_read: false,
      time_ago: '4 hours ago',
    },
    {
      id: 'notif-2',
      title: 'Wallet top-up confirmed',
      message: '₹50 was added to your wallet in this demo.',
      category: 'wallet',
      is_read: true,
      time_ago: '2 days ago',
    },
    {
      id: 'notif-3',
      title: 'DNS record updated',
      message: 'A record for rahul.evocation.in was saved successfully in the demo.',
      category: 'dns',
      is_read: true,
      time_ago: '10 hours ago',
    },
  ]);

  useEffect(() => {
    async function loadNotifications() {
      try {
        const data = await getNotifications();
        if (data && data.length > 0) {
          const mapped: NotificationItem[] = data.map((n: any) => ({
            id: n.id,
            title: n.title || 'Notification',
            message: n.message,
            category: n.category || 'general',
            is_read: n.is_read || false,
            time_ago: 'Recent',
          }));
          setNotifications(mapped);
        }
      } catch {
        // demo defaults
      }
    }
    loadNotifications();
  }, []);

  const handleMarkAsRead = async (id: string) => {
    try {
      await markNotificationRead(id);
    } catch {
      // Local fallback
    }
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
  };

  const handleMarkAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
  };

  const filtered = notifications.filter((n) => {
    if (filterCategory === 'All') return true;
    if (filterCategory === 'Unread') return !n.is_read;
    return n.category.toLowerCase() === filterCategory.toLowerCase();
  });

  return (
    <>
      <header className="border-b border-slate-200 bg-white px-4 py-4 md:px-8">
        <p className="text-sm uppercase tracking-widest text-slate-400">Dashboard</p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">Notifications</h1>
      </header>

      <main className="space-y-6 p-4 md:p-8">
        <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row md:items-center md:justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Notifications</h2>
          <div className="flex gap-2">
            <select
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 focus:outline-none"
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
            >
              <option>All</option>
              <option>Unread</option>
              <option>Wallet</option>
              <option>Rental</option>
              <option>DNS</option>
            </select>
            <button
              onClick={handleMarkAllAsRead}
              className="rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium hover:bg-slate-50 text-slate-700"
            >
              Mark all as read
            </button>
          </div>
        </section>

        {filtered.length === 0 ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-500">
            No notifications found in this category.
          </div>
        ) : (
          filtered.map((item) => (
            <article
              key={item.id}
              className={`rounded-2xl border p-5 shadow-sm transition ${
                !item.is_read
                  ? 'border-indigo-200 bg-indigo-50'
                  : 'border-slate-200 bg-white'
              }`}
            >
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">
                    {item.title}{' '}
                    {!item.is_read && (
                      <span className="rounded-full bg-indigo-600 px-2 py-1 text-[10px] uppercase tracking-widest text-white ml-2">
                        Unread
                      </span>
                    )}
                  </h2>
                  <p className="mt-2 text-sm text-slate-600">{item.message}</p>
                </div>
                <div className="text-right text-xs text-slate-500">
                  <span className="uppercase">{item.category}</span>
                  <p className="mt-2">{item.time_ago}</p>
                </div>
              </div>
              {!item.is_read && (
                <button
                  onClick={() => handleMarkAsRead(item.id)}
                  className="mt-4 rounded-xl border border-indigo-200 bg-white px-3 py-2 text-sm text-indigo-600 font-medium hover:bg-indigo-50"
                >
                  Mark as read
                </button>
              )}
            </article>
          ))
        )}
      </main>
    </>
  );
}

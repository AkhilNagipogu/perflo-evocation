/**
 * Evocation SaaS API Client
 * Type-safe interface to the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('evocation_token');
}

export function setAuthToken(token: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('evocation_token', token);
  }
}

export function clearAuthToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('evocation_token');
    localStorage.removeItem('evocation_user');
  }
}

export function getAdminToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('evocation_admin_token');
}

export function setAdminToken(token: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('evocation_admin_token', token);
  }
}

export function clearAdminToken() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('evocation_admin_token');
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}, isAdmin: boolean = false): Promise<T> {
  const token = isAdmin ? getAdminToken() : getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  const res = await fetch(url, { ...options, headers });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      // Non-json response
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

// ── Public & Pricing ──────────────────────────────────────────────────────────

export async function getPricingPlans() {
  return request<any[]>('/pricing/plans');
}

export async function getParentDomains() {
  return request<any[]>('/pricing/domains');
}

export async function searchSubdomain(subdomainName: string, parentDomainId: string) {
  return request<any>('/rentals/search', {
    method: 'POST',
    body: JSON.stringify({ subdomain_name: subdomainName, parent_domain_id: parentDomainId }),
  });
}

export async function submitAbuseReport(data: {
  reported_domain: string;
  category: string;
  description: string;
  reporter_email?: string;
  reporter_name?: string;
}) {
  return request<any>('/abuse-reports', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function registerUser(data: any) {
  return request<any>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function loginUser(data: any) {
  return request<any>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getMe() {
  return request<any>('/auth/me');
}

// ── Wallet & Payments ────────────────────────────────────────────────────────

export async function getWallet() {
  return request<any>('/wallet');
}

export async function topupWallet(amountPaise: number) {
  return request<any>('/wallet/topup', {
    method: 'POST',
    body: JSON.stringify({ amount_paise: amountPaise }),
  });
}

export async function confirmTestPayment(orderId: string) {
  return request<any>('/payments/confirm-test', {
    method: 'POST',
    body: JSON.stringify({ order_id: orderId }),
  });
}

export async function getTransactions(page: number = 1, pageSize: number = 20) {
  return request<any>(`/wallet/transactions?page=${page}&page_size=${pageSize}`);
}

export async function getWalletSummary() {
  return request<any>('/wallet/summary');
}

// ── Rentals ──────────────────────────────────────────────────────────────────

export async function purchaseRental(data: {
  subdomain_name: string;
  parent_domain_id: string;
  pricing_plan_id: string;
  coupon_code?: string;
  auto_renew?: boolean;
}) {
  return request<any>('/rentals/purchase', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getMyRentals() {
  return request<any>('/rentals/my-rentals');
}

export async function getRental(rentalId: string) {
  return request<any>(`/rentals/${rentalId}`);
}

export async function renameRental(rentalId: string, newSubdomainName: string) {
  return request<any>(`/rentals/${rentalId}/rename`, {
    method: 'POST',
    body: JSON.stringify({ new_subdomain_name: newSubdomainName }),
  });
}

export async function renewRental(rentalId: string, couponCode?: string) {
  return request<any>(`/rentals/${rentalId}/renew`, {
    method: 'POST',
    body: JSON.stringify({ coupon_code: couponCode }),
  });
}

export async function toggleAutoRenew(rentalId: string, autoRenew: boolean) {
  return request<any>(`/rentals/${rentalId}/auto-renew`, {
    method: 'PATCH',
    body: JSON.stringify({ auto_renew: autoRenew }),
  });
}

// ── DNS ──────────────────────────────────────────────────────────────────────

export async function getDnsRecords(rentalId: string) {
  return request<any[]>(`/rentals/${rentalId}/dns`);
}

export async function createDnsRecord(rentalId: string, data: {
  record_type: string;
  content: string;
  ttl?: number;
  proxied?: boolean;
}) {
  return request<any>(`/rentals/${rentalId}/dns`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateDnsRecord(recordId: string, data: {
  content?: string;
  ttl?: number;
  proxied?: boolean;
}) {
  return request<any>(`/dns/${recordId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteDnsRecord(recordId: string) {
  return request<any>(`/dns/${recordId}`, {
    method: 'DELETE',
  });
}

// ── Notifications ────────────────────────────────────────────────────────────

export async function getNotifications() {
  return request<any[]>('/notifications');
}

export async function getUnreadCount() {
  return request<{ unread_count: number }>('/notifications/unread-count');
}

export async function markNotificationRead(id: string) {
  return request<any>(`/notifications/${id}/read`, { method: 'PATCH' });
}

export const getCurrentUser = getMe;
export const logout = clearAuthToken;
export const getRentals = getMyRentals;

export async function releaseRental(rentalId: string) {
  return request<any>(`/rentals/${rentalId}`, {
    method: 'DELETE',
  });
}

// ── Coupons ──────────────────────────────────────────────────────────────────

export async function validateCoupon(code: string, planId: string, amountPaise: number) {
  return request<any>('/coupons/validate', {
    method: 'POST',
    body: JSON.stringify({ code, plan_id: planId, amount_paise: amountPaise }),
  });
}

// ── Admin Endpoints ──────────────────────────────────────────────────────────

export async function adminLogin(data: any) {
  return request<any>('/admin/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getAdminStats() {
  return request<any>('/admin/stats', {}, true);
}

export async function adminListUsers(search?: string) {
  const q = search ? `?search=${encodeURIComponent(search)}` : '';
  return request<any[]>(`/admin/users${q}`, {}, true);
}

export async function adminManageUser(userId: string, action: string, reason?: string) {
  return request<any>(`/admin/users/${userId}/manage`, {
    method: 'POST',
    body: JSON.stringify({ action, reason }),
  }, true);
}

export async function adminListRentals(status?: string, search?: string) {
  const params = new URLSearchParams();
  if (status) params.append('status_filter', status);
  if (search) params.append('search', search);
  return request<any[]>(`/admin/rentals?${params.toString()}`, {}, true);
}

export async function adminManageRental(rentalId: string, action: string, reason: string, extendDays?: number) {
  return request<any>(`/admin/rentals/${rentalId}/manage`, {
    method: 'POST',
    body: JSON.stringify({ action, reason, extend_days: extendDays }),
  }, true);
}

export async function adminAdjustWallet(userId: string, amountPaise: number, reason: string) {
  return request<any>(`/admin/users/${userId}/wallet-adjust`, {
    method: 'POST',
    body: JSON.stringify({ amount_paise: amountPaise, reason }),
  }, true);
}

export async function adminListCoupons() {
  return request<any[]>('/admin/coupons', {}, true);
}

export async function adminCreateCoupon(data: any) {
  return request<any>('/admin/coupons', {
    method: 'POST',
    body: JSON.stringify(data),
  }, true);
}

export async function adminListAbuseReports() {
  return request<any[]>('/admin/abuse-reports', {}, true);
}

export async function adminReviewAbuseReport(reportId: string, data: any) {
  return request<any>(`/admin/abuse-reports/${reportId}/review`, {
    method: 'POST',
    body: JSON.stringify(data),
  }, true);
}

export async function adminGetAuditLogs() {
  return request<any>('/admin/audit-logs', {}, true);
}

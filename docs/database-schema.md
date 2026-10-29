# Database Schema Documentation

## 1. Schema Design Philosophy

The database is built on **PostgreSQL 16** with strong relational integrity, foreign key constraints, and partial unique indexes. All primary keys are UUIDv4 to eliminate enumeration vulnerabilities.

### Integer Currency Handling
All monetary quantities across `wallets`, `wallet_transactions`, `pricing_plans`, `pricing_tiers`, `coupons`, and `payment_orders` are stored as **64-bit integers representing paise** (1 INR = 100 paise):
- ₹60.00 is stored as `6000`
- ₹1,000.00 is stored as `100000`

Floating-point numbers are prohibited in database storage and financial calculations to eliminate rounding inaccuracies.

## 2. Entity Overview & Tables

| Table Name | Description | Key Indexes & Constraints |
| :--- | :--- | :--- |
| `users` | Customer identity and profile | Unique `email`, unique `username` |
| `admin_users` | Platform operators | Unique `email`, role enforcement |
| `parent_domains` | Root zones available for rent | Unique `domain`, `cloudflare_zone_id` |
| `pricing_plans` | Base subscription tiers (₹60/yr for 2) | Unique `slug`, `price_paise` |
| `pricing_tiers` | Tiered expansion pricing | FK to `pricing_plans` |
| `wallets` | Customer prepaid balances | Unique `user_id`, `balance_paise >= 0` |
| `wallet_transactions` | Immutable double-entry ledger | Unique `idempotency_key`, indexed `(user_id, created_at)` |
| `subscriptions` | Bundle entitlements | Tracked `used_subdomains` / `max_subdomains` |
| `rentals` | Subdomain leases | Partial unique index `uq_active_rental_per_subdomain` |
| `rental_name_history` | Audit trail of rename actions | FK to `rentals` and `users` |
| `dns_records` | Cloudflare DNS record mirror | Unique `cloudflare_record_id`, indexed `(rental_id, record_type)` |
| `payment_orders` | Stripe / provider checkouts | Unique `idempotency_key`, `provider_order_id` |
| `coupons` | Promotional discount codes | Unique uppercase `code`, usage counters |
| `coupon_redemptions` | Log of used coupons | Indexed `(coupon_id, user_id)` |
| `notifications` | In-app user notifications | Indexed `(user_id, is_read)` |
| `abuse_reports` | Public incident reports | Unique `reference_id`, indexed `status` |
| `abuse_actions` | Enforcement audit log | FK to `abuse_reports` and `admin_users` |
| `audit_logs` | Immutable operational audit | Indexed `(actor_type, actor_id)`, `created_at` |
| `system_config` | Dynamic key-value settings | Unique `key` |
| `name_reservations` | Temporary checkout locks | Unique `(parent_domain_id, subdomain_name)`, TTL expiration |

## 3. Name Reuse & Partial Unique Indexing

To allow released or cancelled subdomains to be re-rented by other customers while preventing duplicate active rentals, the `rentals` table utilizes a **partial unique index**:

```sql
CREATE UNIQUE INDEX uq_active_rental_per_subdomain 
ON rentals (parent_domain_id, subdomain_name) 
WHERE status NOT IN ('released', 'cancelled');
```

When a rental is released following the 5-day grace period, the record remains for historical auditing, but the subdomain label becomes immediately available for new registrations.

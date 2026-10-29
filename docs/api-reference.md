# API Reference Manual

Base path: `/api/v1`

All responses are formatted in JSON. Protected endpoints require a Bearer token passed in the `Authorization` header:
`Authorization: Bearer <access_token>`

---

## 1. System Health

### `GET /health`
Returns service readiness, database connectivity, and runtime environment.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "timestamp": "2026-10-29T10:00:00Z",
  "database": "connected",
  "environment": "production",
  "payment_provider": "stripe"
}
```

---

## 2. Authentication (`/auth`)

### `POST /auth/register`
Create customer account and initialize prepaid wallet.
- **Request Body**:
```json
{
  "email": "customer@example.com",
  "username": "customer",
  "password": "Password123!",
  "full_name": "Jane Doe"
}
```
- **Response `201 Created`**: Returns customer record.

### `POST /auth/login`
Authenticate user with email and password.
- **Request Body**:
```json
{
  "email": "customer@example.com",
  "password": "Password123!"
}
```
- **Response `200 OK`**:
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### `GET /auth/me`
Retrieve currently authenticated customer profile.

---

## 3. Subdomains & Rentals (`/rentals`)

### `POST /rentals/search`
Search subdomain availability across 6 validation layers (syntax, length, prohibited global names, reserved domain names, active leases, and temporary checkout locks).
- **Request Body**:
```json
{
  "subdomain_name": "myproject",
  "parent_domain_id": "uuid-here"
}
```
- **Response `200 OK`**:
```json
{
  "subdomain_name": "myproject",
  "parent_domain": "example.com",
  "full_domain": "myproject.example.com",
  "is_available": true,
  "price_paise": 6000,
  "price_display": "₹60.00",
  "included_subdomains": 2
}
```

### `POST /rentals/purchase`
Purchase subdomain using wallet balance. If user has available capacity in their 2-subdomain annual bundle, price charged is ₹0.
- **Request Body**:
```json
{
  "subdomain_name": "myproject",
  "parent_domain_id": "uuid-here",
  "pricing_plan_id": "uuid-here",
  "coupon_code": "WELCOME10",
  "auto_renew": true
}
```

### `POST /rentals/{rental_id}/rename`
Rename a subdomain. Preserves expiration date; enforces 24-hour rename cooldown.
- **Request Body**:
```json
{
  "new_subdomain_name": "renamedproject"
}
```

### `POST /rentals/{rental_id}/renew`
Renew rental for 1 year from current expiry date.

---

## 4. Cloudflare DNS Records (`/rentals/{id}/dns` & `/dns/{id}`)

### `GET /rentals/{rental_id}/dns`
List active DNS records for rental.

### `POST /rentals/{rental_id}/dns`
Create DNS record synced to Cloudflare.
- **Request Body**:
```json
{
  "record_type": "A",
  "content": "192.0.2.1",
  "ttl": 3600,
  "proxied": true
}
```

### `PUT /dns/{record_id}`
Update existing DNS record.

### `DELETE /dns/{record_id}`
Delete record from Cloudflare and database.

---

## 5. Wallet & Payments (`/wallet` & `/payments`)

### `GET /wallet`
Get current balance in paise and formatted INR display.

### `POST /wallet/topup`
Initiate wallet topup order.
- **Request Body**:
```json
{
  "amount_paise": 6000
}
```

### `GET /wallet/transactions`
List immutable ledger transaction history with pagination.

### `POST /payments/webhook/stripe`
Stripe webhook listener verifying signature header and crediting wallet.

---

## 6. Administration (`/admin`)

### `POST /admin/login`
Admin authentication returning admin-scoped token.

### `GET /admin/stats`
Dashboard metrics: total users, active rentals, grace period, float in paise, pending abuse.

### `POST /admin/users/{id}/manage`
Suspend (`suspend`), restore (`unsuspend`), or manual email verification (`verify_email`).

### `POST /admin/rentals/{id}/manage`
Extend expiry (`extend`), suspend (`suspend`), restore (`restore`), or release (`release`).

### `POST /admin/users/{id}/wallet-adjust`
Credit or debit wallet with mandatory reason and immutable audit log entry.

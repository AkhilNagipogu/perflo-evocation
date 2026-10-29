# Evocation Platform Architecture

## 1. System Overview

**Evocation** is a production-oriented SaaS platform engineered for automated subdomain rentals and programmatic Cloudflare DNS management.

```
                              ┌────────────────────────────────────────┐
                              │            Caddy Reverse Proxy         │
                              │       (Automated TLS / Port 80/443)    │
                              └──────────────────┬─────────────────────┘
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        │                                                 │
            ┌───────────▼───────────┐                         ┌───────────▼───────────┐
            │   Customer Frontend   │                         │    Admin Dashboard    │
            │ (Next.js 14 App /:3000)│                        │(Dedicated Host /:3000)│
            └───────────┬───────────┘                         └───────────┬───────────┘
                        │                                                 │
                        └────────────────────────┬────────────────────────┘
                                                 │ /api/*
                                     ┌───────────▼───────────┐
                                     │   FastAPI Backend     │
                                     │   (Python 3.12 /:8000)│
                                     └─────┬───────┬───────┬─┘
                                           │       │       │
                ┌──────────────────────────┘       │       └──────────────────────────┐
                │                                  │                                  │
    ┌───────────▼───────────┐          ┌───────────▼───────────┐          ┌───────────▼───────────┐
    │  PostgreSQL Database  │          │  Cloudflare DNS v4    │          │  Payment & Stripe API │
    │   (Relational Ledger) │          │  (Real Edge Records)  │          │   (Webhook Verified)  │
    └───────────────────────┘          └───────────────────────┘          └───────────────────────┘
```

## 2. Core Architectural Principles

1. **Prepaid Wallet Ledger**: All customer balances and transactions are tracked in immutable, integer paise units (1 INR = 100 paise). Balances are never modified directly without an associated transaction record and idempotency key.
2. **Strict Subdomain Lifecycle**: Rentals transition deterministically from `RESERVED` -> `ACTIVE` -> `EXPIRED` -> `GRACE_PERIOD` -> `RELEASED`. A strict 5-day (120-hour) grace period prevents accidental loss while freeing dormant names.
3. **Real Cloudflare Integration**: DNS records (A, AAAA, CNAME, TXT) are synchronized directly with the Cloudflare API v4 server-side. Secrets are never exposed to the client.
4. **Host and Role Isolation**: Administrative capabilities and endpoints are segregated by role and accessible via independent hostnames or dedicated admin credentials.
5. **Separation of Payments and Wallet Credit**: Wallet crediting occurs exclusively through authenticated server-side webhooks with cryptographic signature verification, never client-side redirects.

## 3. Technology Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (asyncio + asyncpg), Alembic, Pydantic v2, APScheduler.
- **Frontend**: Next.js 14 (App Router), TypeScript, Vanilla CSS design system.
- **Database**: PostgreSQL 16 (production) with strict foreign keys and partial unique indexing.
- **Reverse Proxy**: Caddy 2 with automated ACME certificate provisioning (ZeroSSL / Let's Encrypt).

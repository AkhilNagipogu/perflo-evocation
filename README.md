# Evocation — Subdomain Rental Platform

Evocation is a full-stack, production-grade SaaS platform built to automate the leasing, billing, lifecycle management, and Cloudflare DNS routing of custom subdomains.

## Key Features & Business Model

- **Base Subscription Bundle**: ₹60/year for **2 subdomains** total (stored in integer paise as 6,000 paise).
- **Prepaid Wallet Architecture**: Double-entry ledger with balance checks, idempotency keys, and minimum first-funding enforcement (₹60.00).
- **Strict 5-Day Grace Period**: Guaranteed 120-hour grace period upon expiration with automated DNS suspension and name release handling.
- **Real Cloudflare DNS API**: Server-side synchronization of `A`, `AAAA`, `CNAME`, and `TXT` records with optional Cloudflare DDoS and CDN proxying (Orange Cloud).
- **Subdomain Renaming**: Change subdomain labels while preserving the original subscription expiration date, protected by a 24-hour cooldown.
- **Promotional Coupons**: Percentage and fixed-amount discounts with usage counters and plan limits.
- **Abuse Reporting & Triage**: Public reporting system with reference codes and one-click administrative domain suspension.
- **Administrative Control Center**: Dedicated dashboard for monitoring financial float, user management, manual wallet adjustments, and immutable audit logs.

---

## Technology Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0 (asyncio + asyncpg), Alembic, Pydantic v2, APScheduler.
- **Frontend**: Next.js 14 (App Router), TypeScript, Vanilla CSS design system.
- **Database**: PostgreSQL 16 with partial unique indexes (`uq_active_rental_per_subdomain`).
- **Payments**: Stripe API v12 with webhook cryptographic signature verification (and isolated dev test provider).
- **DNS**: Cloudflare API v4.
- **Reverse Proxy**: Caddy 2 with automated Let's Encrypt / ZeroSSL TLS certificates.

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI REST endpoints (auth, rentals, wallet, dns, admin, etc.)
│   │   ├── core/            # Database engine, JWT security, pydantic settings, dependencies
│   │   ├── jobs/            # Background tasks (expirations, renewals, reminders, reservations)
│   │   ├── models/          # 20 SQLAlchemy declarative models
│   │   ├── providers/       # Cloudflare API v4, Stripe payments, multi-provider email
│   │   ├── schemas/         # Pydantic request and response schemas
│   │   ├── services/        # Core business logic services
│   │   └── main.py          # FastAPI application entry point with security middleware
│   ├── migrations/          # Async Alembic migrations
│   ├── tests/               # Comprehensive Pytest automated test suite
│   ├── alembic.ini          # Alembic configuration
│   ├── pyproject.toml
│   └── requirements.txt     # Pinned Python dependencies
├── frontend/
│   ├── app/                 # Next.js 14 App Router pages (Landing, Login, Dashboard, DNS, Admin)
│   ├── lib/                 # Type-safe API client
│   ├── next.config.js       # Standalone build and API rewrite config
│   ├── package.json
│   └── tsconfig.json
├── deploy/
│   ├── Caddyfile            # Production reverse proxy and TLS configuration
│   ├── Dockerfile.backend   # Multi-stage Python 3.12 runner with unprivileged user
│   ├── Dockerfile.frontend  # Multi-stage Node 20 standalone runner
│   ├── docker-compose.yml   # Development compose file
│   └── docker-compose.prod.yml # Production compose file
├── scripts/
│   ├── backup.sh            # Automated pg_dump backup with gzip compression and retention
│   ├── restore.sh           # Database restoration script
│   ├── health_check.sh      # Service health verification script
│   └── seed_data.py         # Seed script for initial admin, base plan, and root domain
└── docs/                    # Architecture, deployment, schema, and API documentation
```

---

## Quick Start (Local Development)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env

# Run database migrations
alembic upgrade head

# Seed base plan, root domain, and admin user
python ../scripts/seed_data.py

# Start backend server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` for the customer portal and `http://localhost:3000/admin` for the administrative console.

---

## Production Deployment (Linux Server)

For complete production deployment instructions using Docker Compose and Caddy on a Linux server, refer to:
👉 [Production Deployment Guide](docs/deployment.md)

```bash
# Build and launch production stack
docker compose -f deploy/docker-compose.prod.yml up -d --build

# Run initial migrations and seed data
docker compose -f deploy/docker-compose.prod.yml exec backend alembic upgrade head
docker compose -f deploy/docker-compose.prod.yml exec backend python scripts/seed_data.py
```

---

## Technical Documentation

- [System Architecture](docs/architecture.md)
- [Database Schema & Money Handling](docs/database-schema.md)
- [API Reference Manual](docs/api-reference.md)
- [Subdomain Lifecycle & 5-Day Grace Period](docs/subdomain-lifecycle.md)
- [Prepaid Wallet & Payment Processing](docs/payments-and-wallet.md)
- [Cloudflare DNS Integration Manual](docs/cloudflare-integration.md)
- [Administrator Operations Guide](docs/admin-guide.md)
- [Architectural Decision Records (ADRs)](docs/decisions/)

---

## License

Proprietary — Evocation. All rights reserved.

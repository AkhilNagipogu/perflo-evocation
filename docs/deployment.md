# Production Deployment Guide

This guide walks you through deploying the **Evocation Subdomain Platform** onto a clean Linux server (Ubuntu 22.04 LTS or 24.04 LTS).

## 1. Prerequisites

- A Linux server with at least 2 vCPUs, 4GB RAM, and 20GB SSD storage.
- Standard ports open in server firewall: `80` (HTTP), `443` (HTTPS), and `22` (SSH).
- Docker and Docker Compose v2 installed.
- DNS A records configured pointing to your server IP:
  - `example.com` (public customer site)
  - `admin.example.com` (administrative dashboard)

## 2. Server Setup & Repository Setup

```bash
# Update server packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ufw

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Clone the repository
git clone https://github.com/your-org/perflo.evocation.git /opt/evocation
cd /opt/evocation
```

## 3. Configuration (`.env`)

Copy the environment template and edit with production credentials:

```bash
cp .env.example .env
nano .env
```

Ensure the following variables are configured:
```ini
APP_ENV=production
PUBLIC_DOMAIN=example.com
ADMIN_DOMAIN=admin.example.com
ACME_EMAIL=admin@example.com

# Database passwords
POSTGRES_DB=evocation
POSTGRES_USER=evocation_admin
POSTGRES_PASSWORD=GENERATE_STRONG_SECRET_PASSWORD

# Security keys
APP_SECRET_KEY=GENERATE_LONG_HEX_SECRET
JWT_SECRET_KEY=GENERATE_LONG_HEX_SECRET

# Cloudflare API Token (Zone:DNS:Edit permission)
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_ZONE_MAP={"your_zone_id":"example.com"}

# Stripe Production Keys
PAYMENT_PROVIDER=stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

## 4. Launch Production Containers

```bash
# Build and launch production stack (Caddy, Postgres, Backend, Frontend)
docker compose -f deploy/docker-compose.prod.yml up -d --build

# Verify container statuses
docker compose -f deploy/docker-compose.prod.yml ps
```

## 5. Run Database Migrations & Seed Data

```bash
# Apply initial schema migrations
docker compose -f deploy/docker-compose.prod.yml exec backend alembic upgrade head

# Seed initial admin account, base pricing plan (₹60/yr), and root domains
docker compose -f deploy/docker-compose.prod.yml exec backend python scripts/seed_data.py
```

## 6. Configure Daily Automated Backups

Add the backup script to system crontab:

```bash
sudo chmod +x scripts/backup.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/evocation/scripts/backup.sh >> /var/log/evocation_backup.log 2>&1") | crontab -
```

## 7. Post-Deployment Verification

Run the automated health check script:
```bash
./scripts/health_check.sh
```

Navigate to:
- Public site: `https://example.com`
- Admin dashboard: `https://admin.example.com` (Log in with credentials seeded in step 5)

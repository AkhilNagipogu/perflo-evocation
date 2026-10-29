# Prflo by Evocation — Production Launch Checklist & Operator Guide

This document is the official pre-flight and launch operational guide for deploying **Prflo by Evocation** to production.

---

## 1. Pre-Flight Configuration Checklist

Before running the deployment script, verify that the following accounts and credentials are ready:

### A. Root Domain & Cloudflare DNS
1. **Root Zone Delegation**: Point your primary domain (e.g. `perflo.in` or `evocation.in`) nameservers to Cloudflare.
2. **Cloudflare API Token**:
   - Go to **Cloudflare Dashboard → My Profile → API Tokens → Create Token**.
   - Use the **Edit zone DNS** template.
   - Permissions: `Zone - DNS - Edit` and `Zone - Zone - Read`.
   - Zone Resources: `Include - Specific Zone - <your_root_domain>`.
   - Copy the API token and the Zone ID (found on the zone overview page).
3. **Server DNS Records**:
   - Create an `A` record for your public site: e.g. `perflo.in` → `<your-server-ip>` (DNS-only / grey-clouded or proxied through Caddy).
   - Create an `A` record for your admin portal: e.g. `admin.perflo.in` → `<your-server-ip>`.

### B. Payment Gateway (Stripe / Razorpay)
1. **Stripe Live Credentials**:
   - Obtain `STRIPE_SECRET_KEY` (`sk_live_...`) and `STRIPE_PUBLISHABLE_KEY` (`pk_live_...`).
2. **Webhook Registration**:
   - In Stripe Dashboard → Developers → Webhooks, add endpoint:
     `https://<your-public-domain>/api/v1/payments/webhook`
   - Select events: `checkout.session.completed`, `payment_intent.succeeded`, `payment_intent.payment_failed`.
   - Copy the Signing Secret to `STRIPE_WEBHOOK_SECRET` (`whsec_...`).

### C. Transactional Email (Postmark, SendGrid, Resend, or AWS SES)
- Set `EMAIL_PROVIDER=smtp`
- Configure `SMTP_HOST`, `SMTP_PORT=587`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `EMAIL_FROM_ADDRESS` (`notifications@<your-domain>`).

---

## 2. Server Provisioning & Setup (Ubuntu 22.04 / 24.04 LTS)

SSH into your clean Linux server:

```bash
# 1. Update system packages & install Docker
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ufw
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Configure Firewall (UFW)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# 3. Clone Repository
sudo git clone https://github.com/your-org/perflo.evocation.git /opt/evocation
sudo chown -R $USER:$USER /opt/evocation
cd /opt/evocation
```

---

## 3. Production Environment File (`.env`)

Create `.env` from template:

```bash
cp .env.example .env
nano .env
```

Set the production variables:

```ini
APP_ENV=production
PUBLIC_DOMAIN=perflo.in
ADMIN_DOMAIN=admin.perflo.in
ACME_EMAIL=admin@perflo.in

# Database
POSTGRES_DB=evocation
POSTGRES_USER=evocation_admin
POSTGRES_PASSWORD=YOUR_STRONG_SECRET_PASSWORD

# Security
APP_SECRET_KEY=GENERATE_64_CHAR_HEX_KEY
JWT_SECRET_KEY=GENERATE_64_CHAR_HEX_KEY

# Cloudflare
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token
CLOUDFLARE_ZONES=your_zone_id:perflo.in

# Payments
PAYMENT_PROVIDER=stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CURRENCY=inr

# Email
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.postmarkapp.com
SMTP_PORT=587
SMTP_USERNAME=your_smtp_token
SMTP_PASSWORD=your_smtp_token
EMAIL_FROM_ADDRESS=notifications@perflo.in
```

---

## 4. Launch with Single Command

Run the deployment script:

```bash
chmod +x scripts/deploy.sh scripts/health_check.sh scripts/backup.sh
./scripts/deploy.sh
```

The script will:
1. Build optimized Next.js frontend with standalone output.
2. Build minimal, multi-stage Python 3.12 backend container.
3. Launch PostgreSQL 16 database with health monitoring.
4. Launch Caddy reverse proxy with automated Let's Encrypt TLS certificates.
5. Automatically bootstrap database tables, root parent domain, base pricing plan (₹60/yr), and initial administrator credentials.
6. Verify live container health.

---

## 5. Automated Backups & Maintenance

Set up the automated daily database backup cron job:

```bash
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/evocation/scripts/backup.sh >> /var/log/evocation_backup.log 2>&1") | crontab -
```

Backups are compressed with gzip and retained for 30 days automatically in `/var/backups/evocation`.

---

## 6. Post-Launch Smoke Tests

1. **Public Site**: Open `https://<PUBLIC_DOMAIN>/` in browser. Verify SSL certificate lock and hero subdomain search.
2. **Search Availability**: Test searching for an available name (e.g. `mysite`). Verify instant availability check.
3. **Register Customer**: Create a new test user account and log into customer dashboard.
4. **Top Up Wallet**: Test funding wallet with minimum ₹60.00 first-time funding.
5. **Purchase Rental**: Claim a subdomain and check that DNS records provision seamlessly.
6. **Admin Dashboard**: Open `https://<ADMIN_DOMAIN>/` or `/admin` and log in with your super admin credentials. Verify metrics and audit log feed.

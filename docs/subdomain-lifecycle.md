# Subdomain Lifecycle & Expiration Policy

## 1. Lifecycle State Machine

A subdomain rental transitions deterministically through 6 formal lifecycle states:

```
[ RESERVED ] ────────► [ ACTIVE ] ────────► [ EXPIRED / GRACE_PERIOD ] ────────► [ RELEASED ]
     │                     │                            │
     ▼ (TTL Expiry)        ▼ (Abuse)                    ▼ (Renewal Paid)
[ CANCELLED ]         [ SUSPENDED ] ──────────────► [ ACTIVE ]
```

### State Definitions
1. **`RESERVED`**: Temporary lock held during checkout (default TTL: 15 minutes). Prevents concurrent checkouts from racing on the same subdomain.
2. **`ACTIVE`**: Fully paid and operational. Cloudflare DNS records are synced and resolving globally.
3. **`EXPIRED / GRACE_PERIOD`**: Subscription period has ended. The user has **5 full days (120 hours)** to renew without losing ownership.
   - During grace period: DNS records are suspended from Cloudflare.
   - The original customer retains exclusive renewal rights.
4. **`SUSPENDED`**: Administrative intervention due to verified abuse or terms violation. DNS records deactivated.
5. **`RELEASED`**: 5-day grace period has expired without payment. Subdomain name is released back to the public pool and can be registered by any user.
6. **`CANCELLED`**: Checkout reservation expired or terminated before purchase completion.

## 2. Strict 5-Day Grace Period Implementation

The platform's background job scheduler runs every 10 minutes to process expirations:

```python
# Transition to Grace Period when expires_at reached
if rental.expires_at <= now and rental.status == RentalStatus.ACTIVE:
    rental.status = RentalStatus.EXPIRED
    rental.grace_period_ends_at = rental.expires_at + timedelta(days=5)
    await dns_service.suspend_all_rental_records(rental.id)
    await notify_grace_period(rental)

# Transition to Released when grace_period_ends_at reached
if rental.grace_period_ends_at <= now and rental.status in (RentalStatus.EXPIRED, RentalStatus.GRACE_PERIOD):
    rental.status = RentalStatus.RELEASED
    await dns_service.suspend_all_rental_records(rental.id)
    await notify_name_released(rental)
```

## 3. Renaming Policy & Cooldown

- Renaming an active rental replaces `subdomain_name` and updates the Cloudflare DNS host.
- **Expiry Date Preservation**: Renaming does **not** change, extend, or reset `expires_at`.
- **24-Hour Cooldown**: To prevent rapid churn and DNS flapping, a strict 24-hour cooldown is enforced after each rename.
- Every rename is recorded in the `rental_name_history` table for auditing and tracking.

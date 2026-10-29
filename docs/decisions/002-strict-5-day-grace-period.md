# ADR 002: Strict 5-Day Grace Period Implementation

## Status
Accepted

## Context
When a customer's annual subdomain subscription expires, deleting or releasing the name immediately causes catastrophic domain hijacking or broken deployments if the renewal was delayed by bank processing or oversight. Conversely, holding expired domains indefinitely prevents new customers from acquiring dormant names.

## Decision
Implement a strict, automated **5-day (120-hour) grace period**:
1. When `expires_at` is reached without renewal, the rental status transitions to `EXPIRED`.
2. Active DNS records are suspended from Cloudflare to prevent unmonitored traffic.
3. The original customer retains exclusive renewal rights.
4. When `grace_period_ends_at` is reached (exactly `expires_at + 5 days`), the status transitions to `RELEASED`.
5. Released names are freed for re-registration via partial unique indexes.

## Consequences
- Protects customers from accidental instant name loss.
- Ensures predictable release times for interested new customers.
- Automates lifecycle handling without manual administrative intervention.

# Prepaid Wallet & Payment Processing

## 1. Prepaid Wallet Model

Evocation operates exclusively on a **prepaid wallet balance model**. Customers deposit funds into their wallet, from which subscription purchases, renewals, and bundle upgrades are debited with millisecond latency and row-level database locking (`SELECT ... FOR UPDATE`).

### Business Rules & Bounds
- **Currency**: Indian Rupees (INR), stored and processed exclusively in **integer paise** (100 paise = ₹1.00).
- **First-Time Funding Minimum**: **₹60.00** (6,000 paise). Prevents micro-fraud and covers the exact cost of an initial 2-subdomain annual bundle.
- **Subsequent Top-Up Bounds**: ₹60.00 minimum up to ₹1,000.00 (100,000 paise) maximum.
- **No Negative Balances**: Debits verify balance integrity atomically. Overdrafts are rejected with `ValueError("Insufficient wallet balance")`.

## 2. Double-Entry Immutable Ledger

Every financial movement generates an immutable record in `wallet_transactions`:

```sql
CREATE TABLE wallet_transactions (
    id UUID PRIMARY KEY,
    wallet_id UUID NOT NULL,
    user_id UUID NOT NULL,
    reference_id VARCHAR(64) NOT NULL,
    transaction_type VARCHAR(32) NOT NULL, -- wallet_funding, subscription_purchase, subscription_renewal, admin_adjustment, refund
    amount_paise INTEGER NOT NULL,          -- Positive for credit, negative for debit
    balance_after_paise INTEGER NOT NULL,
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Idempotency
All credit and debit operations require an `idempotency_key`. If a network retry or duplicate webhook payload is received with an identical key, the transaction is recognized and the existing state returned without double-crediting or double-debiting.

## 3. Stripe Payment Gateway Integration

1. **Checkout Initiation**: When the customer tops up their wallet, FastAPI creates a Stripe Checkout Session with `metadata: {"order_id": order.id, "user_id": user.id}`.
2. **Server-Side Webhook Processing**:
   - The customer is redirected to a pending screen.
   - **The wallet is NEVER credited upon browser redirect**.
   - Credit occurs only when Stripe dispatches `checkout.session.completed` to `/api/v1/payments/webhook/stripe`.
   - The webhook signature (`Stripe-Signature`) is verified cryptographically against `STRIPE_WEBHOOK_SECRET`.
3. **Test Payment Isolation**:
   - The test provider is strictly forbidden in production (`APP_ENV=production`), raising a `RuntimeError` if invoked.

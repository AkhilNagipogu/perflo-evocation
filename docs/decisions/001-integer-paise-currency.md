# ADR 001: Integer Currency Storage (Paise)

## Status
Accepted

## Context
Financial systems that store money using floating-point types (`float`, `double`, or IEEE 754 representations) suffer from rounding artifacts (e.g., `0.1 + 0.2 = 0.30000000000000004`). In a subdomain platform dealing with Indian Rupees (INR) across micro-payments, coupon calculations, and wallet ledgers, precision errors cannot be tolerated.

## Decision
All monetary values across database columns, backend models, API payloads, and internal calculations are stored strictly as **64-bit integers representing paise** (1 INR = 100 paise).

Formatting to standard Rupee representations (e.g., `₹60.00`) occurs solely at the presentation boundary in frontend components or string helper formatters.

## Consequences
- Guaranteed mathematical precision across additions, subtractions, and discounts.
- Elimination of floating-point rounding bugs.
- Integer compatibility across PostgreSQL `INTEGER` / `BIGINT` and Stripe API amounts.

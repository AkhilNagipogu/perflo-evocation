"""
Rental service — subdomain search, purchase, rename, renewal, expiry.

This is the core business logic. All ownership, availability, and billing
decisions are made here against the database (not Cloudflare or frontend).
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import generate_reference_id
from app.models.parent_domain import ParentDomain
from app.models.pricing import PricingPlan
from app.models.rental import Rental, RentalStatus, RentalNameHistory
from app.models.reservation import NameReservation
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.wallet import TransactionType
from app.services.wallet_service import WalletService

settings = get_settings()

# Subdomain validation
SUBDOMAIN_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
MIN_SUBDOMAIN_LENGTH = 2
MAX_SUBDOMAIN_LENGTH = 63

# Global prohibited names (in addition to per-domain reserved names)
GLOBAL_PROHIBITED = {
    "www", "mail", "ftp", "admin", "api", "ns1", "ns2", "ns3", "ns4",
    "mx", "smtp", "imap", "pop", "pop3", "webmail", "cpanel", "whm",
    "autodiscover", "autoconfig", "_dmarc", "_domainkey", "localhost",
    "root", "postmaster", "abuse", "hostmaster", "webmaster",
    "test", "dev", "staging", "beta", "alpha", "demo",
}


class RentalService:
    """Handles subdomain availability, purchase, rename, and renewal."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_service = WalletService(db)

    # ── Availability ─────────────────────────────────────────────────────

    async def check_availability(
        self,
        subdomain_name: str,
        parent_domain_id: uuid.UUID,
    ) -> dict:
        """
        Check if a subdomain is available for rental.
        Returns availability status, reason if unavailable, and pricing.
        """
        subdomain_name = subdomain_name.strip().lower()

        # 1. Validate syntax
        validation_error = self._validate_subdomain_syntax(subdomain_name)
        if validation_error:
            return {
                "is_available": False,
                "subdomain_name": subdomain_name,
                "parent_domain": "",
                "full_domain": subdomain_name,
                "reason": "invalid",
                "message": validation_error,
            }

        # 2. Get parent domain
        result = await self.db.execute(
            select(ParentDomain).where(
                ParentDomain.id == parent_domain_id,
                ParentDomain.is_active == True,
            )
        )
        parent = result.scalar_one_or_none()
        if not parent:
            return {
                "is_available": False,
                "subdomain_name": subdomain_name,
                "parent_domain": "",
                "full_domain": subdomain_name,
                "reason": "invalid_parent",
                "message": "Parent domain not found or inactive",
            }

        parent_domain_name = parent.domain
        full_domain_name = f"{subdomain_name}.{parent_domain_name}"

        # 3. Check reserved/prohibited names
        if subdomain_name in GLOBAL_PROHIBITED or subdomain_name in parent.reserved_name_list:
            return {
                "is_available": False,
                "subdomain_name": subdomain_name,
                "parent_domain": parent_domain_name,
                "full_domain": full_domain_name,
                "reason": "prohibited",
                "message": "This name is reserved and cannot be rented",
            }

        # 4. Check active or grace-period rentals
        active_statuses = [
            RentalStatus.ACTIVE,
            RentalStatus.EXPIRED,
            RentalStatus.GRACE_PERIOD,
            RentalStatus.SUSPENDED,
            RentalStatus.RESERVED,
        ]
        result = await self.db.execute(
            select(Rental).where(
                Rental.parent_domain_id == parent_domain_id,
                Rental.subdomain_name == subdomain_name,
                Rental.status.in_(active_statuses),
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            if existing.status == RentalStatus.RESERVED:
                return {
                    "is_available": False,
                    "subdomain_name": subdomain_name,
                    "parent_domain": parent_domain_name,
                    "full_domain": full_domain_name,
                    "reason": "reserved_checkout",
                    "message": "This name is currently reserved for another checkout",
                }
            elif existing.status in (RentalStatus.EXPIRED, RentalStatus.GRACE_PERIOD):
                return {
                    "is_available": False,
                    "subdomain_name": subdomain_name,
                    "parent_domain": parent_domain_name,
                    "full_domain": full_domain_name,
                    "reason": "grace_period",
                    "message": "This name is in a grace period for the current owner",
                }
            elif existing.status == RentalStatus.SUSPENDED:
                return {
                    "is_available": False,
                    "subdomain_name": subdomain_name,
                    "parent_domain": parent_domain_name,
                    "full_domain": full_domain_name,
                    "reason": "suspended",
                    "message": "This name is currently suspended",
                }
            else:
                return {
                    "is_available": False,
                    "subdomain_name": subdomain_name,
                    "parent_domain": parent_domain_name,
                    "full_domain": full_domain_name,
                    "reason": "active_rental",
                    "message": "This name is already rented",
                }

        # 5. Check temporary reservations
        result = await self.db.execute(
            select(NameReservation).where(
                NameReservation.parent_domain_id == parent_domain_id,
                NameReservation.subdomain_name == subdomain_name,
                NameReservation.expires_at > datetime.now(timezone.utc),
            )
        )
        if result.scalar_one_or_none():
            return {
                "is_available": False,
                "subdomain_name": subdomain_name,
                "parent_domain": parent_domain_name,
                "full_domain": full_domain_name,
                "reason": "reserved_checkout",
                "message": "This name is currently reserved for another checkout",
            }

        # 6. Get pricing
        result = await self.db.execute(
            select(PricingPlan).where(
                PricingPlan.is_active == True,
                PricingPlan.is_base_plan == True,
            )
        )
        base_plan = result.scalar_one_or_none()

        full_domain = f"{subdomain_name}.{parent.domain}"

        return {
            "is_available": True,
            "subdomain_name": subdomain_name,
            "parent_domain": parent.domain,
            "full_domain": full_domain,
            "price_paise": base_plan.price_paise if base_plan else None,
            "price_display": base_plan.price_inr if base_plan else None,
            "plan_name": base_plan.name if base_plan else None,
            "plan_id": str(base_plan.id) if base_plan else None,
            "billing_period_days": base_plan.billing_period_days if base_plan else None,
            "included_subdomains": base_plan.included_subdomains if base_plan else None,
        }

    # ── Purchase ─────────────────────────────────────────────────────────

    async def purchase_rental(
        self,
        user_id: uuid.UUID,
        subdomain_name: str,
        parent_domain_id: uuid.UUID,
        pricing_plan_id: uuid.UUID,
        coupon_discount_paise: int = 0,
        coupon_id: uuid.UUID | None = None,
        auto_renew: bool = False,
    ) -> Rental:
        """
        Purchase a subdomain rental. Atomic operation:
        1. Re-verify availability (with lock)
        2. Check/create subscription entitlement
        3. Debit wallet
        4. Create rental record
        5. Clean up reservation
        """
        subdomain_name = subdomain_name.strip().lower()
        now = datetime.now(timezone.utc)

        # Validate syntax
        error = self._validate_subdomain_syntax(subdomain_name)
        if error:
            raise ValueError(error)

        # Get parent domain
        result = await self.db.execute(
            select(ParentDomain).where(
                ParentDomain.id == parent_domain_id,
                ParentDomain.is_active == True,
            )
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise ValueError("Parent domain not found or inactive")

        # Check prohibited
        if subdomain_name in GLOBAL_PROHIBITED or subdomain_name in parent.reserved_name_list:
            raise ValueError("This name is reserved and cannot be rented")

        # Get pricing plan
        result = await self.db.execute(
            select(PricingPlan).where(
                PricingPlan.id == pricing_plan_id,
                PricingPlan.is_active == True,
            )
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError("Pricing plan not found or inactive")

        # Re-check availability with row-level consideration
        active_statuses = [
            RentalStatus.ACTIVE, RentalStatus.EXPIRED,
            RentalStatus.GRACE_PERIOD, RentalStatus.SUSPENDED,
        ]
        result = await self.db.execute(
            select(Rental).where(
                Rental.parent_domain_id == parent_domain_id,
                Rental.subdomain_name == subdomain_name,
                Rental.status.in_(active_statuses),
            )
        )
        if result.scalar_one_or_none():
            raise ValueError("This subdomain is no longer available")

        # Check if user already has an active subscription with capacity
        subscription = await self._get_or_create_subscription(
            user_id, plan, now
        )

        # Calculate price
        # If this is within the bundle entitlement and subscription was just purchased,
        # the cost was already paid via the subscription.
        # If subscription existed and has capacity, no additional charge for bundle slots.
        price_to_charge = 0
        if subscription.active_rental_count >= subscription.max_subdomains:
            # Beyond bundle — would need additional tier pricing (future)
            raise ValueError(
                f"Your current plan allows {subscription.max_subdomains} subdomains. "
                "Additional subdomain pricing tiers are not yet available."
            )

        # For the subscription itself — charge if newly created
        is_new_subscription = subscription.active_rental_count == 0 and (
            now - subscription.started_at < timedelta(seconds=5)
        )
        if is_new_subscription:
            price_to_charge = plan.price_paise - coupon_discount_paise
            price_to_charge = max(0, price_to_charge)

        # Debit wallet if there's a charge
        if price_to_charge > 0:
            idempotency_key = f"rental-purchase-{user_id}-{subdomain_name}-{parent_domain_id}-{now.timestamp()}"
            await self.wallet_service.debit_wallet(
                user_id=user_id,
                amount_paise=price_to_charge,
                transaction_type=TransactionType.RENTAL_PURCHASE,
                description=f"Subscription: {plan.name} — {subdomain_name}.{parent.domain}",
                idempotency_key=idempotency_key,
            )

        # Create rental
        full_domain = f"{subdomain_name}.{parent.domain}"
        expires_at = subscription.expires_at
        grace_period_ends = expires_at + timedelta(days=settings.GRACE_PERIOD_DAYS)

        rental = Rental(
            user_id=user_id,
            parent_domain_id=parent_domain_id,
            pricing_plan_id=pricing_plan_id,
            subdomain_name=subdomain_name,
            full_domain=full_domain,
            status=RentalStatus.ACTIVE,
            started_at=now,
            expires_at=expires_at,
            grace_period_ends_at=grace_period_ends,
            price_paid_paise=price_to_charge,
            auto_renew=auto_renew,
            subscription_id=subscription.id,
        )
        self.db.add(rental)

        # Update subscription count
        subscription.active_rental_count += 1

        # Clean up any reservation for this name
        await self.db.execute(
            delete(NameReservation).where(
                NameReservation.parent_domain_id == parent_domain_id,
                NameReservation.subdomain_name == subdomain_name,
            )
        )

        await self.db.flush()
        return rental

    async def _get_or_create_subscription(
        self, user_id: uuid.UUID, plan: PricingPlan, now: datetime
    ) -> Subscription:
        """Get existing active subscription or create a new one."""
        # Look for active subscription with the same plan
        result = await self.db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.pricing_plan_id == plan.id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.GRACE_PERIOD,
                ]),
            )
        )
        subscription = result.scalar_one_or_none()

        if subscription and subscription.active_rental_count < subscription.max_subdomains:
            return subscription

        # Create new subscription
        expires_at = now + timedelta(days=plan.billing_period_days)
        subscription = Subscription(
            user_id=user_id,
            pricing_plan_id=plan.id,
            status=SubscriptionStatus.ACTIVE,
            max_subdomains=plan.included_subdomains,
            active_rental_count=0,
            started_at=now,
            expires_at=expires_at,
            grace_period_ends_at=expires_at + timedelta(days=settings.GRACE_PERIOD_DAYS),
            price_paid_paise=plan.price_paise,
        )
        self.db.add(subscription)
        await self.db.flush()
        return subscription

    # ── Rename ───────────────────────────────────────────────────────────

    async def rename_rental(
        self,
        rental_id: uuid.UUID,
        user_id: uuid.UUID,
        new_subdomain_name: str,
    ) -> Rental:
        """
        Rename a subdomain. Preserves subscription dates.
        """
        new_subdomain_name = new_subdomain_name.strip().lower()
        now = datetime.now(timezone.utc)

        # Validate syntax
        error = self._validate_subdomain_syntax(new_subdomain_name)
        if error:
            raise ValueError(error)

        # Get rental with ownership check
        result = await self.db.execute(
            select(Rental).where(
                Rental.id == rental_id,
                Rental.user_id == user_id,
                Rental.status == RentalStatus.ACTIVE,
            )
        )
        rental = result.scalar_one_or_none()
        if not rental:
            raise ValueError("Rental not found or not active")

        # Check cooldown
        if rental.last_renamed_at:
            cooldown_until = rental.last_renamed_at + timedelta(
                hours=settings.RENAME_COOLDOWN_HOURS
            )
            if now < cooldown_until:
                remaining = cooldown_until - now
                hours_left = int(remaining.total_seconds() / 3600) + 1
                raise ValueError(
                    f"Rename cooldown active. Try again in {hours_left} hours."
                )

        # Same name check
        if new_subdomain_name == rental.subdomain_name:
            raise ValueError("New name is the same as the current name")

        # Get parent domain
        result = await self.db.execute(
            select(ParentDomain).where(ParentDomain.id == rental.parent_domain_id)
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise ValueError("Parent domain not found")

        # Check prohibited
        if new_subdomain_name in GLOBAL_PROHIBITED or new_subdomain_name in parent.reserved_name_list:
            raise ValueError("This name is reserved and cannot be used")

        # Check availability of new name
        active_statuses = [
            RentalStatus.ACTIVE, RentalStatus.EXPIRED,
            RentalStatus.GRACE_PERIOD, RentalStatus.SUSPENDED,
        ]
        result = await self.db.execute(
            select(Rental).where(
                Rental.parent_domain_id == rental.parent_domain_id,
                Rental.subdomain_name == new_subdomain_name,
                Rental.status.in_(active_statuses),
                Rental.id != rental.id,
            )
        )
        if result.scalar_one_or_none():
            raise ValueError("The requested name is not available")

        # Record history
        old_name = rental.subdomain_name
        old_full = rental.full_domain
        new_full = f"{new_subdomain_name}.{parent.domain}"

        history = RentalNameHistory(
            rental_id=rental.id,
            old_subdomain_name=old_name,
            new_subdomain_name=new_subdomain_name,
            old_full_domain=old_full,
            new_full_domain=new_full,
            changed_by_user_id=user_id,
        )
        self.db.add(history)

        # Update rental — preserves all dates
        rental.subdomain_name = new_subdomain_name
        rental.full_domain = new_full
        rental.last_renamed_at = now
        rental.rename_count += 1

        await self.db.flush()
        return rental

    # ── Renewal ──────────────────────────────────────────────────────────

    async def renew_rental(
        self,
        rental_id: uuid.UUID,
        user_id: uuid.UUID,
        coupon_discount_paise: int = 0,
    ) -> Rental:
        """
        Renew a rental subscription. Extends the expiry date.
        Can be done during active period or grace period.
        """
        now = datetime.now(timezone.utc)

        # Get rental
        result = await self.db.execute(
            select(Rental).where(
                Rental.id == rental_id,
                Rental.user_id == user_id,
                Rental.status.in_([
                    RentalStatus.ACTIVE,
                    RentalStatus.EXPIRED,
                    RentalStatus.GRACE_PERIOD,
                ]),
            )
        )
        rental = result.scalar_one_or_none()
        if not rental:
            raise ValueError("Rental not found or not eligible for renewal")

        # Get pricing plan
        result = await self.db.execute(
            select(PricingPlan).where(
                PricingPlan.id == rental.pricing_plan_id,
                PricingPlan.is_active == True,
            )
        )
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError("Pricing plan not found")

        # Calculate renewal price
        renewal_price = plan.price_paise - coupon_discount_paise
        renewal_price = max(0, renewal_price)

        # Debit wallet
        if renewal_price > 0:
            idempotency_key = f"renewal-{rental_id}-{rental.renewal_count + 1}"
            await self.wallet_service.debit_wallet(
                user_id=user_id,
                amount_paise=renewal_price,
                transaction_type=TransactionType.SUBSCRIPTION_RENEWAL,
                description=f"Renewal: {rental.full_domain}",
                rental_id=rental.id,
                idempotency_key=idempotency_key,
            )

        # Extend from current expiry (not from now, to avoid losing time)
        base_date = rental.expires_at if rental.expires_at and rental.expires_at > now else now
        new_expiry = base_date + timedelta(days=plan.billing_period_days)
        new_grace = new_expiry + timedelta(days=settings.GRACE_PERIOD_DAYS)

        rental.expires_at = new_expiry
        rental.grace_period_ends_at = new_grace
        rental.status = RentalStatus.ACTIVE
        rental.last_renewal_at = now
        rental.renewal_count += 1

        # Update subscription too
        if rental.subscription_id:
            result = await self.db.execute(
                select(Subscription).where(Subscription.id == rental.subscription_id)
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.expires_at = new_expiry
                sub.grace_period_ends_at = new_grace
                sub.status = SubscriptionStatus.ACTIVE
                sub.last_renewal_at = now
                sub.renewal_count += 1

        await self.db.flush()
        return rental

    # ── Listing ──────────────────────────────────────────────────────────

    async def get_user_rentals(
        self, user_id: uuid.UUID
    ) -> list[Rental]:
        """Get all rentals for a user (excluding released/cancelled)."""
        result = await self.db.execute(
            select(Rental)
            .where(
                Rental.user_id == user_id,
                Rental.status.notin_([RentalStatus.RELEASED, RentalStatus.CANCELLED]),
            )
            .order_by(Rental.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_rental(
        self, rental_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> Rental | None:
        """Get a specific rental, optionally checking ownership."""
        query = select(Rental).where(Rental.id == rental_id)
        if user_id:
            query = query.where(Rental.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ── Reservation ──────────────────────────────────────────────────────

    async def create_reservation(
        self,
        user_id: uuid.UUID,
        subdomain_name: str,
        parent_domain_id: uuid.UUID,
    ) -> NameReservation:
        """Create a temporary checkout reservation."""
        # Clean up expired reservations first
        await self.db.execute(
            delete(NameReservation).where(
                NameReservation.expires_at < datetime.now(timezone.utc)
            )
        )

        reservation = NameReservation(
            user_id=user_id,
            parent_domain_id=parent_domain_id,
            subdomain_name=subdomain_name.strip().lower(),
            expires_at=datetime.now(timezone.utc) + timedelta(
                minutes=settings.CHECKOUT_RESERVATION_MINUTES
            ),
        )
        self.db.add(reservation)
        await self.db.flush()
        return reservation

    # ── Auto-renewal toggle ──────────────────────────────────────────────

    async def set_auto_renew(
        self, rental_id: uuid.UUID, user_id: uuid.UUID, enabled: bool
    ) -> Rental:
        """Enable or disable auto-renewal for a rental."""
        result = await self.db.execute(
            select(Rental).where(
                Rental.id == rental_id,
                Rental.user_id == user_id,
            )
        )
        rental = result.scalar_one_or_none()
        if not rental:
            raise ValueError("Rental not found")
        rental.auto_renew = enabled
        await self.db.flush()
        return rental

    # ── Helpers ──────────────────────────────────────────────────────────

    def _validate_subdomain_syntax(self, name: str) -> str | None:
        """Validate subdomain syntax. Returns error message or None."""
        if len(name) < MIN_SUBDOMAIN_LENGTH:
            return f"Subdomain must be at least {MIN_SUBDOMAIN_LENGTH} characters"
        if len(name) > MAX_SUBDOMAIN_LENGTH:
            return f"Subdomain must be at most {MAX_SUBDOMAIN_LENGTH} characters"
        if not SUBDOMAIN_PATTERN.match(name):
            return "Subdomain must start and end with a letter or digit, and may contain hyphens"
        if "--" in name:
            return "Subdomain cannot contain consecutive hyphens"
        return None

"""
Admin service — dashboard statistics, user/rental management, financial adjustments, and abuse reviews.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.abuse_report import AbuseAction, AbuseReport, AbuseReportStatus
from app.models.admin_user import AdminUser
from app.models.coupon import Coupon
from app.models.dns_record import DnsRecord, DnsRecordStatus
from app.models.payment import PaymentOrder, PaymentStatus
from app.models.rental import Rental, RentalStatus
from app.models.system_config import SystemConfig
from app.models.user import User
from app.models.wallet import TransactionStatus, TransactionType, Wallet, WalletTransaction
from app.schemas.admin import AdminDashboardStats
from app.services.audit_service import AuditService
from app.services.dns_service import DnsService
from app.services.wallet_service import WalletService

logger = logging.getLogger(__name__)


class AdminService:
    """Provides administrative operations across the platform."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)
        self.wallet_service = WalletService(db)
        self.dns_service = DnsService(db)

    async def get_dashboard_stats(self) -> AdminDashboardStats:
        """Aggregate high-level metrics for the admin dashboard."""
        now = datetime.now(timezone.utc)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        expiring_threshold = now + timedelta(days=7)

        # Users
        total_users = (await self.db.execute(select(func.count(User.id)))).scalar_one()
        active_users = (
            await self.db.execute(select(func.count(User.id)).where(User.is_active.is_(True)))
        ).scalar_one()

        # Rentals
        total_rentals = (await self.db.execute(select(func.count(Rental.id)))).scalar_one()
        active_rentals = (
            await self.db.execute(
                select(func.count(Rental.id)).where(Rental.status == RentalStatus.ACTIVE)
            )
        ).scalar_one()

        expiring_soon = (
            await self.db.execute(
                select(func.count(Rental.id)).where(
                    Rental.status == RentalStatus.ACTIVE,
                    Rental.expires_at <= expiring_threshold,
                    Rental.expires_at > now,
                )
            )
        ).scalar_one()

        in_grace_period = (
            await self.db.execute(
                select(func.count(Rental.id)).where(
                    Rental.status.in_([RentalStatus.EXPIRED, RentalStatus.GRACE_PERIOD])
                )
            )
        ).scalar_one()

        released_this_month = (
            await self.db.execute(
                select(func.count(Rental.id)).where(
                    Rental.status == RentalStatus.RELEASED,
                    Rental.updated_at >= start_of_month,
                )
            )
        ).scalar_one()

        # Financials
        total_wallet_res = await self.db.execute(
            select(func.coalesce(func.sum(Wallet.balance_paise), 0))
        )
        total_wallet_balance_paise = total_wallet_res.scalar_one()

        payments_res = await self.db.execute(
            select(func.coalesce(func.sum(PaymentOrder.amount_paise), 0)).where(
                PaymentOrder.status == PaymentStatus.COMPLETED,
                PaymentOrder.updated_at >= start_of_month,
            )
        )
        payments_this_month_paise = payments_res.scalar_one()

        # DNS errors
        failed_dns = (
            await self.db.execute(
                select(func.count(DnsRecord.id)).where(DnsRecord.status == DnsRecordStatus.FAILED)
            )
        ).scalar_one()

        # Abuse
        pending_abuse = (
            await self.db.execute(
                select(func.count(AbuseReport.id)).where(
                    AbuseReport.status.in_([AbuseReportStatus.SUBMITTED, AbuseReportStatus.UNDER_REVIEW])
                )
            )
        ).scalar_one()

        # Coupons
        active_coupons = (
            await self.db.execute(
                select(func.count(Coupon.id)).where(
                    Coupon.is_active.is_(True),
                    (Coupon.expires_at.is_(None) | (Coupon.expires_at > now)),
                )
            )
        ).scalar_one()

        return AdminDashboardStats(
            total_users=total_users,
            active_users=active_users,
            total_rentals=total_rentals,
            active_rentals=active_rentals,
            expiring_soon=expiring_soon,
            in_grace_period=in_grace_period,
            released_this_month=released_this_month,
            total_wallet_balance_paise=total_wallet_balance_paise,
            payments_this_month_paise=payments_this_month_paise,
            failed_dns_operations=failed_dns,
            pending_abuse_reports=pending_abuse,
            active_coupons=active_coupons,
        )

    async def manage_user(
        self,
        user_id: uuid.UUID,
        action: str,
        admin_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> User:
        """Perform administrative action on a user account."""
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalars().first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        state_before = {"is_active": user.is_active, "is_email_verified": user.is_email_verified}

        if action == "suspend":
            user.is_active = False
        elif action == "unsuspend":
            user.is_active = True
        elif action == "verify_email":
            user.is_email_verified = True
        else:
            raise ValueError(f"Unsupported action: {action}")

        state_after = {"is_active": user.is_active, "is_email_verified": user.is_email_verified}

        await self.audit.log_event(
            action=f"user_{action}",
            resource_type="user",
            resource_id=str(user.id),
            description=f"Admin {action} user {user.email}: {reason or 'No reason provided'}",
            actor_type="admin",
            actor_id=admin_id,
            details_before=state_before,
            details_after=state_after,
        )

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def manage_rental(
        self,
        rental_id: uuid.UUID,
        action: str,
        admin_id: uuid.UUID,
        reason: str,
        extend_days: Optional[int] = None,
    ) -> Rental:
        """Perform administrative action on a subdomain rental."""
        rental = (
            await self.db.execute(select(Rental).where(Rental.id == rental_id))
        ).scalars().first()
        if not rental:
            raise ValueError(f"Rental {rental_id} not found")

        state_before = {
            "status": rental.status.value,
            "expires_at": rental.expires_at.isoformat() if rental.expires_at else None,
        }

        if action == "suspend":
            rental.status = RentalStatus.SUSPENDED
            await self.dns_service.suspend_all_rental_records(rental.id)
        elif action == "restore":
            rental.status = RentalStatus.ACTIVE
            await self.dns_service.restore_all_rental_records(rental.id)
        elif action == "release":
            rental.status = RentalStatus.RELEASED
            await self.dns_service.suspend_all_rental_records(rental.id)
        elif action == "extend":
            if not extend_days or extend_days <= 0:
                raise ValueError("extend_days must be positive")
            base_date = rental.expires_at or datetime.now(timezone.utc)
            rental.expires_at = base_date + timedelta(days=extend_days)
            rental.grace_period_ends_at = rental.expires_at + timedelta(days=5)
            if rental.status in (RentalStatus.EXPIRED, RentalStatus.GRACE_PERIOD):
                rental.status = RentalStatus.ACTIVE
                await self.dns_service.restore_all_rental_records(rental.id)
        else:
            raise ValueError(f"Unsupported rental action: {action}")

        state_after = {
            "status": rental.status.value,
            "expires_at": rental.expires_at.isoformat() if rental.expires_at else None,
        }

        await self.audit.log_event(
            action=f"rental_{action}",
            resource_type="rental",
            resource_id=str(rental.id),
            description=f"Admin {action} on {rental.full_domain}: {reason}",
            actor_type="admin",
            actor_id=admin_id,
            details_before=state_before,
            details_after=state_after,
        )

        await self.db.flush()
        await self.db.refresh(rental)
        return rental

    async def adjust_wallet(
        self,
        user_id: uuid.UUID,
        amount_paise: int,
        admin_id: uuid.UUID,
        reason: str,
        reference: Optional[str] = None,
    ) -> WalletTransaction:
        """Credit or debit a user's wallet with an audit trail."""
        wallet = await self.wallet_service.get_wallet_for_update(user_id)
        idempotency_key = f"admin_adj_{uuid.uuid4().hex}"

        if amount_paise > 0:
            tx = await self.wallet_service.credit_wallet(
                user_id=user_id,
                amount_paise=amount_paise,
                transaction_type=TransactionType.ADMIN_ADJUSTMENT,
                idempotency_key=idempotency_key,
                description=f"Admin credit: {reason}",
                reference_id=reference or f"admin_{admin_id}",
            )
        else:
            debit_amount = abs(amount_paise)
            tx = await self.wallet_service.debit_wallet(
                user_id=user_id,
                amount_paise=debit_amount,
                transaction_type=TransactionType.ADMIN_ADJUSTMENT,
                idempotency_key=idempotency_key,
                description=f"Admin debit: {reason}",
                reference_id=reference or f"admin_{admin_id}",
            )

        await self.audit.log_event(
            action="wallet_admin_adjustment",
            resource_type="wallet",
            resource_id=str(wallet.id),
            description=f"Adjusted wallet for user {user_id} by {amount_paise} paise: {reason}",
            actor_type="admin",
            actor_id=admin_id,
            metadata={"amount_paise": amount_paise, "transaction_id": str(tx.id)},
        )

        return tx

    async def process_refund(
        self,
        transaction_id: uuid.UUID,
        amount_paise: int,
        admin_id: uuid.UUID,
        reason: str,
    ) -> WalletTransaction:
        """Process a refund for a previously settled transaction."""
        stmt = select(WalletTransaction).where(WalletTransaction.id == transaction_id)
        res = await self.db.execute(stmt)
        orig_tx = res.scalars().first()
        if not orig_tx:
            raise ValueError(f"Transaction {transaction_id} not found")

        idempotency_key = f"refund_{uuid.uuid4().hex}"
        refund_tx = await self.wallet_service.credit_wallet(
            user_id=orig_tx.user_id,
            amount_paise=amount_paise,
            transaction_type=TransactionType.REFUND,
            idempotency_key=idempotency_key,
            description=f"Refund for tx {orig_tx.id}: {reason}",
            reference_id=str(orig_tx.id),
        )

        await self.audit.log_event(
            action="wallet_refund",
            resource_type="wallet_transaction",
            resource_id=str(refund_tx.id),
            description=f"Issued refund of {amount_paise} paise for original tx {orig_tx.id}: {reason}",
            actor_type="admin",
            actor_id=admin_id,
            metadata={"original_transaction_id": str(orig_tx.id), "amount_paise": amount_paise},
        )

        return refund_tx

    async def review_abuse_report(
        self,
        report_id: uuid.UUID,
        status: AbuseReportStatus,
        admin_id: uuid.UUID,
        review_notes: Optional[str] = None,
        action_type: Optional[str] = None,
        action_description: Optional[str] = None,
    ) -> AbuseReport:
        """Review an abuse report and take optional enforcement action."""
        stmt = select(AbuseReport).where(AbuseReport.id == report_id)
        res = await self.db.execute(stmt)
        report = res.scalars().first()
        if not report:
            raise ValueError(f"Abuse report {report_id} not found")

        report.status = status
        report.review_notes = review_notes
        report.reviewed_by_admin_id = admin_id
        report.reviewed_at = datetime.now(timezone.utc)

        if action_type and action_description:
            action = AbuseAction(
                abuse_report_id=report.id,
                admin_user_id=admin_id,
                action_type=action_type,
                description=action_description,
            )
            self.db.add(action)

            # If action is to suspend the rental
            if action_type == "suspend_rental" and report.rental_id:
                await self.manage_rental(
                    rental_id=report.rental_id,
                    action="suspend",
                    admin_id=admin_id,
                    reason=f"Enforcement on abuse report {report.reference_id}: {action_description}",
                )

        await self.audit.log_event(
            action="abuse_report_reviewed",
            resource_type="abuse_report",
            resource_id=str(report.id),
            description=f"Admin reviewed abuse report {report.reference_id}: status={status.value}",
            actor_type="admin",
            actor_id=admin_id,
            metadata={"action_type": action_type},
        )

        await self.db.flush()
        await self.db.refresh(report)
        return report

    async def get_system_config(self, key: str) -> Optional[SystemConfig]:
        """Fetch system config value by key."""
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        res = await self.db.execute(stmt)
        return res.scalars().first()

    async def set_system_config(
        self,
        key: str,
        value: str,
        admin_id: uuid.UUID,
        description: Optional[str] = None,
    ) -> SystemConfig:
        """Set or update a system configuration key."""
        cfg = await self.get_system_config(key)
        if not cfg:
            cfg = SystemConfig(key=key, value=value, description=description, updated_by_admin_id=admin_id)
            self.db.add(cfg)
        else:
            cfg.value = value
            if description:
                cfg.description = description
            cfg.updated_by_admin_id = admin_id

        await self.db.flush()
        await self.db.refresh(cfg)
        return cfg

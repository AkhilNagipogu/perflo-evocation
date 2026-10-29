"""
Wallet service — all monetary operations with concurrency safety.

All amounts are in integer paise. No floating-point arithmetic for money.
Uses SELECT FOR UPDATE to prevent double-spending.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import generate_reference_id
from app.models.wallet import Wallet, WalletTransaction, TransactionType, TransactionStatus

settings = get_settings()


class WalletService:
    """Handles all wallet operations with transactional safety."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_wallet(self, user_id: uuid.UUID) -> Wallet:
        """Get wallet for a user."""
        result = await self.db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        wallet = result.scalar_one_or_none()
        if not wallet:
            raise ValueError("Wallet not found")
        return wallet

    async def get_wallet_for_update(self, user_id: uuid.UUID) -> Wallet:
        """Get wallet with row lock for safe mutation."""
        result = await self.db.execute(
            select(Wallet)
            .where(Wallet.user_id == user_id)
            .with_for_update()
        )
        wallet = result.scalar_one_or_none()
        if not wallet:
            raise ValueError("Wallet not found")
        return wallet

    async def validate_topup_amount(
        self, amount_paise: int, wallet: Wallet
    ) -> None:
        """Validate top-up amount against configured rules."""
        # First funding minimum
        if not wallet.has_been_funded:
            if amount_paise < settings.WALLET_FIRST_FUNDING_MIN_PAISE:
                raise ValueError(
                    f"Minimum first-time wallet funding is ₹{settings.WALLET_FIRST_FUNDING_MIN_PAISE // 100}"
                )

        if amount_paise <= 0:
            raise ValueError("Amount must be positive")

        if amount_paise > settings.WALLET_MAX_TOPUP_PAISE:
            raise ValueError(
                f"Maximum top-up is ₹{settings.WALLET_MAX_TOPUP_PAISE // 100}"
            )

        if amount_paise < settings.WALLET_MIN_TOPUP_PAISE:
            raise ValueError(
                f"Minimum top-up is ₹{settings.WALLET_MIN_TOPUP_PAISE // 100}"
            )

    async def credit_wallet(
        self,
        user_id: uuid.UUID,
        amount_paise: int,
        transaction_type: TransactionType,
        description: str = "Wallet credit",
        payment_order_id: uuid.UUID | None = None,
        coupon_id: uuid.UUID | None = None,
        admin_user_id: uuid.UUID | None = None,
        admin_reason: str | None = None,
        idempotency_key: str | None = None,
        reference_id: str | None = None,
    ) -> WalletTransaction:
        """
        Credit the wallet. Uses SELECT FOR UPDATE for safety.
        Returns the created transaction.
        """
        # Check idempotency
        if idempotency_key:
            existing = await self.db.execute(
                select(WalletTransaction).where(
                    WalletTransaction.idempotency_key == idempotency_key
                )
            )
            existing_txn = existing.scalar_one_or_none()
            if existing_txn:
                return existing_txn  # Already processed

        # Lock wallet row
        wallet = await self.get_wallet_for_update(user_id)

        new_balance = wallet.balance_paise + amount_paise
        wallet.balance_paise = new_balance

        if transaction_type == TransactionType.WALLET_FUNDING and not wallet.has_been_funded:
            wallet.has_been_funded = True

        txn = WalletTransaction(
            wallet_id=wallet.id,
            reference_id=reference_id or generate_reference_id("TXN"),
            transaction_type=transaction_type,
            status=TransactionStatus.COMPLETED,
            amount_paise=amount_paise,
            balance_after_paise=new_balance,
            description=description,
            payment_order_id=payment_order_id,
            coupon_id=coupon_id,
            admin_user_id=admin_user_id,
            admin_reason=admin_reason,
            idempotency_key=idempotency_key,
        )
        self.db.add(txn)
        await self.db.flush()
        return txn

    async def debit_wallet(
        self,
        user_id: uuid.UUID,
        amount_paise: int,
        transaction_type: TransactionType,
        description: str,
        rental_id: uuid.UUID | None = None,
        idempotency_key: str | None = None,
        admin_user_id: uuid.UUID | None = None,
        admin_reason: str | None = None,
        reference_id: str | None = None,
    ) -> WalletTransaction:
        """
        Debit the wallet. Checks sufficient balance. Uses SELECT FOR UPDATE.
        amount_paise should be a positive number; it will be stored as negative.
        """
        if amount_paise <= 0:
            raise ValueError("Debit amount must be positive")

        # Check idempotency
        if idempotency_key:
            existing = await self.db.execute(
                select(WalletTransaction).where(
                    WalletTransaction.idempotency_key == idempotency_key
                )
            )
            existing_txn = existing.scalar_one_or_none()
            if existing_txn:
                return existing_txn

        # Lock wallet row
        wallet = await self.get_wallet_for_update(user_id)

        if wallet.balance_paise < amount_paise:
            raise ValueError(
                f"Insufficient balance. Required: ₹{amount_paise // 100}, "
                f"Available: ₹{wallet.balance_paise // 100}"
            )

        new_balance = wallet.balance_paise - amount_paise
        wallet.balance_paise = new_balance

        txn = WalletTransaction(
            wallet_id=wallet.id,
            reference_id=reference_id or generate_reference_id("TXN"),
            transaction_type=transaction_type,
            status=TransactionStatus.COMPLETED,
            amount_paise=-amount_paise,  # Stored as negative for debits
            balance_after_paise=new_balance,
            description=description,
            rental_id=rental_id,
            admin_user_id=admin_user_id,
            admin_reason=admin_reason,
            idempotency_key=idempotency_key,
        )
        self.db.add(txn)
        await self.db.flush()
        return txn

    async def get_transactions(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        transaction_type: TransactionType | None = None,
    ) -> tuple[list[WalletTransaction], int]:
        """Get paginated transaction history."""
        wallet = await self.get_wallet(user_id)

        query = select(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet.id
        )

        if transaction_type:
            query = query.where(
                WalletTransaction.transaction_type == transaction_type
            )

        # Count
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginated results
        query = query.order_by(WalletTransaction.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        transactions = list(result.scalars().all())

        return transactions, total

    async def get_monthly_summary(
        self, user_id: uuid.UUID
    ) -> dict:
        """Get current month spending and funding totals."""
        wallet = await self.get_wallet(user_id)
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Month spending (negative amounts = debits)
        spending_result = await self.db.execute(
            select(func.coalesce(func.sum(WalletTransaction.amount_paise), 0))
            .where(
                and_(
                    WalletTransaction.wallet_id == wallet.id,
                    WalletTransaction.amount_paise < 0,
                    WalletTransaction.status == TransactionStatus.COMPLETED,
                    WalletTransaction.created_at >= month_start,
                )
            )
        )
        month_spending = abs(spending_result.scalar() or 0)

        # Month funding (positive credits from wallet_funding)
        funding_result = await self.db.execute(
            select(func.coalesce(func.sum(WalletTransaction.amount_paise), 0))
            .where(
                and_(
                    WalletTransaction.wallet_id == wallet.id,
                    WalletTransaction.transaction_type == TransactionType.WALLET_FUNDING,
                    WalletTransaction.status == TransactionStatus.COMPLETED,
                    WalletTransaction.created_at >= month_start,
                )
            )
        )
        month_funding = funding_result.scalar() or 0

        return {
            "balance_paise": wallet.balance_paise,
            "month_spending_paise": month_spending,
            "month_funding_paise": month_funding,
        }

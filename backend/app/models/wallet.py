"""
Wallet and transaction ledger models.

All monetary values are stored in integer paise (1 INR = 100 paise).
No floating-point arithmetic is used for money.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

import enum


class TransactionType(str, enum.Enum):
    """Types of wallet transactions."""
    WALLET_FUNDING = "wallet_funding"
    RENTAL_PURCHASE = "rental_purchase"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    REFUND = "refund"
    ADMIN_ADJUSTMENT = "admin_adjustment"
    PROMOTIONAL_CREDIT = "promotional_credit"
    REVERSAL = "reversal"


class TransactionStatus(str, enum.Enum):
    """Status of a wallet transaction."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class Wallet(Base):
    """Customer wallet with prepaid balance in paise."""

    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True, nullable=False, index=True,
    )

    # Balance in paise — authoritative, updated transactionally
    balance_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Track whether this wallet has ever been funded
    has_been_funded: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="wallet")
    transactions: Mapped[list["WalletTransaction"]] = relationship(
        "WalletTransaction", back_populates="wallet", lazy="noload",
        order_by="WalletTransaction.created_at.desc()",
    )

    @property
    def balance_inr(self) -> str:
        """Format balance as INR."""
        rupees = self.balance_paise // 100
        paise = self.balance_paise % 100
        if paise:
            return f"₹{rupees}.{paise:02d}"
        return f"₹{rupees}"

    def __repr__(self) -> str:
        return f"<Wallet user={self.user_id} balance={self.balance_inr}>"


class WalletTransaction(Base):
    """
    Immutable ledger entry for every wallet operation.
    Historical records are never modified to correct errors — 
    instead, compensating entries (reversals) are created.
    """

    __tablename__ = "wallet_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    reference_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType), nullable=False, index=True
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), nullable=False, default=TransactionStatus.COMPLETED
    )

    # Amount in paise — positive for credits, negative for debits
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    # Balance after this transaction (snapshot for auditing)
    balance_after_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    description: Mapped[str] = mapped_column(String(512), nullable=False)

    # Optional references
    rental_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("rentals.id", ondelete="SET NULL"), nullable=True
    )
    payment_order_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("payment_orders.id", ondelete="SET NULL"), nullable=True
    )
    coupon_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True
    )

    # For admin adjustments
    admin_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )
    admin_reason: Mapped[str | None] = mapped_column(Text)

    # Idempotency key to prevent duplicate transactions
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions")

    __table_args__ = (
        Index("ix_wallet_transactions_wallet_created", "wallet_id", "created_at"),
        Index("ix_wallet_transactions_type_created", "transaction_type", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<WalletTransaction {self.reference_id} {self.transaction_type.value} {self.amount_paise}>"

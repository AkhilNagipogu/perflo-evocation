"""
Payment order model — tracks payment provider interactions.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PaymentStatus(str, enum.Enum):
    """Payment order status."""
    CREATED = "created"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    EXPIRED = "expired"


class PaymentOrder(Base):
    """
    Represents a payment intent/order with the payment provider.
    Separated from wallet transactions — a completed payment creates a wallet credit.
    """

    __tablename__ = "payment_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("wallets.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Provider info
    provider: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # "stripe", "test"
    provider_order_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )  # e.g., Stripe checkout session ID
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # e.g., Stripe payment intent ID

    # Amount
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="inr")

    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.CREATED
    )

    # Idempotency key for webhook processing
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )

    # Webhook tracking
    webhook_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    webhook_event_id: Mapped[str | None] = mapped_column(String(255))

    # Refund tracking
    refund_amount_paise: Mapped[int] = mapped_column(Integer, default=0)
    refund_reason: Mapped[str | None] = mapped_column(Text)

    # Metadata
    description: Mapped[str | None] = mapped_column(String(512))
    metadata_json: Mapped[str | None] = mapped_column(Text)  # JSON

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_payment_orders_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<PaymentOrder {self.id} {self.status.value} {self.amount_paise}>"

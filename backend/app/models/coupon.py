"""
Coupon and redemption models.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
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


class Coupon(Base):
    """Administrator-managed discount coupon."""

    __tablename__ = "coupons"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text)

    # Discount type: "percentage" or "fixed"
    discount_type: Mapped[str] = mapped_column(
        String(16), nullable=False
    )

    # Discount value:
    # - For percentage: 10 = 10%
    # - For fixed: value in paise
    discount_value: Mapped[int] = mapped_column(Integer, nullable=False)

    # Validity
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usage limits
    max_uses: Mapped[int | None] = mapped_column(Integer)  # Total uses
    max_uses_per_user: Mapped[int] = mapped_column(Integer, default=1)
    current_uses: Mapped[int] = mapped_column(Integer, default=0)

    # Minimum purchase (paise)
    min_purchase_paise: Mapped[int] = mapped_column(Integer, default=0)

    # Eligible products (JSON array of plan slugs, or null for all)
    eligible_plans: Mapped[str | None] = mapped_column(Text)

    # Created by admin
    created_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Coupon {self.code} {self.discount_type}={self.discount_value}>"


class CouponRedemption(Base):
    """Record of a coupon being used."""

    __tablename__ = "coupon_redemptions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    coupon_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("coupons.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    rental_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("rentals.id", ondelete="SET NULL"), nullable=True
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )

    # Actual discount applied (paise)
    discount_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_coupon_redemptions_coupon_user", "coupon_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<CouponRedemption coupon={self.coupon_id} user={self.user_id}>"

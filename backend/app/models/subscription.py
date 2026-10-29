"""
Subscription model — groups rentals into billing bundles.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SubscriptionStatus(str, enum.Enum):
    """Subscription states."""
    ACTIVE = "active"
    EXPIRED = "expired"
    GRACE_PERIOD = "grace_period"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class Subscription(Base):
    """
    A subscription bundle — e.g., the base plan entitling 2 subdomains.
    Rentals belong to subscriptions.
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    pricing_plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pricing_plans.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[SubscriptionStatus] = mapped_column(
        SAEnum(SubscriptionStatus), nullable=False, default=SubscriptionStatus.ACTIVE
    )

    # Entitlement
    max_subdomains: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    active_rental_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Dates
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    grace_period_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Renewal
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    renewal_count: Mapped[int] = mapped_column(Integer, default=0)
    last_renewal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Price at time of purchase/renewal (paise)
    price_paid_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    rentals: Mapped[list["Rental"]] = relationship(
        "Rental", backref="subscription_ref", lazy="selectin",
        foreign_keys="Rental.subscription_id",
    )

    __table_args__ = (
        Index("ix_subscriptions_user_status", "user_id", "status"),
        Index("ix_subscriptions_expires", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.id} user={self.user_id} status={self.status.value}>"

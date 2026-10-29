"""
Pricing models — configurable plans and tiers.

All monetary values are stored in integer paise (1 INR = 100 paise).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PricingPlan(Base):
    """A pricing plan (e.g. 'Base Bundle' with 2 subdomains for ₹60/year)."""

    __tablename__ = "pricing_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text)

    # Pricing in paise (integer)
    price_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    # What the plan includes
    included_subdomains: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    # Billing period in days (365 = 1 year)
    billing_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_base_plan: Mapped[bool] = mapped_column(Boolean, default=False)

    # Ordering for display
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def price_inr(self) -> str:
        """Format price as INR string."""
        rupees = self.price_paise // 100
        paise = self.price_paise % 100
        if paise:
            return f"₹{rupees}.{paise:02d}"
        return f"₹{rupees}"

    def __repr__(self) -> str:
        return f"<PricingPlan {self.slug} {self.price_inr}>"


class PricingTier(Base):
    """Additional subdomain pricing tiers (for future use)."""

    __tablename__ = "pricing_tiers"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(Text)

    # Price per additional subdomain in paise
    price_per_subdomain_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    # How many additional subdomains this tier covers
    subdomain_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    billing_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=365)

    # Optional: restrict to specific parent domains
    parent_domain_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("parent_domains.id"), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<PricingTier {self.slug}>"

"""
Rental model — the core business entity representing a subdomain rental.
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
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RentalStatus(str, enum.Enum):
    """Rental lifecycle states."""
    RESERVED = "reserved"       # Temporary checkout reservation
    ACTIVE = "active"           # Paid and active
    EXPIRED = "expired"         # Past expiry, in grace period
    GRACE_PERIOD = "grace_period"  # Alias for expired within grace window
    SUSPENDED = "suspended"     # Suspended by admin (abuse)
    RELEASED = "released"       # Grace period ended, name available
    CANCELLED = "cancelled"     # Cancelled by admin/system


class Rental(Base):
    """A subdomain rental — the core business record."""

    __tablename__ = "rentals"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    parent_domain_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("parent_domains.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    pricing_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("pricing_plans.id", ondelete="SET NULL"),
        nullable=True,
    )

    # The subdomain label (e.g., "mysite" for "mysite.example.com")
    subdomain_name: Mapped[str] = mapped_column(
        String(63), nullable=False, index=True
    )

    # Full FQDN for convenience (e.g., "mysite.example.com")
    full_domain: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )

    status: Mapped[RentalStatus] = mapped_column(
        SAEnum(RentalStatus), nullable=False, default=RentalStatus.RESERVED, index=True,
    )

    # Subscription dates — server-generated, never from browser
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    grace_period_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Price paid (snapshot at purchase time, in paise)
    price_paid_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Auto-renewal
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)
    last_renewal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    renewal_count: Mapped[int] = mapped_column(Integer, default=0)

    # Rename tracking
    last_renamed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rename_count: Mapped[int] = mapped_column(Integer, default=0)

    # Cloudflare references
    cloudflare_record_ids: Mapped[str | None] = mapped_column(Text)  # JSON array

    # Bundle tracking — which subscription/bundle this belongs to
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="rentals")
    parent_domain: Mapped["ParentDomain"] = relationship(
        "ParentDomain", back_populates="rentals"
    )
    dns_records: Mapped[list["DnsRecord"]] = relationship(
        "DnsRecord", back_populates="rental", lazy="selectin",
        cascade="all, delete-orphan",
    )
    name_history: Mapped[list["RentalNameHistory"]] = relationship(
        "RentalNameHistory", back_populates="rental", lazy="noload",
        order_by="RentalNameHistory.changed_at.desc()",
    )

    __table_args__ = (
        # Partial unique index: only non-released and non-cancelled rentals must have unique (parent_domain, subdomain)
        # This allows released or cancelled names to be re-rented by other users
        Index(
            "uq_active_rental_per_subdomain",
            "parent_domain_id",
            "subdomain_name",
            unique=True,
            postgresql_where=text("status NOT IN ('released', 'cancelled')"),
            sqlite_where=text("status NOT IN ('released', 'cancelled')"),
        ),
        Index("ix_rentals_user_status", "user_id", "status"),
    )

    @property
    def is_within_grace_period(self) -> bool:
        """Check if rental is within the grace period."""
        if not self.grace_period_ends_at:
            return False
        return datetime.now(tz=self.grace_period_ends_at.tzinfo) < self.grace_period_ends_at

    def __repr__(self) -> str:
        return f"<Rental {self.full_domain} status={self.status.value}>"


class RentalNameHistory(Base):
    """Track name changes for audit purposes."""

    __tablename__ = "rental_name_history"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    rental_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("rentals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    old_subdomain_name: Mapped[str] = mapped_column(String(63), nullable=False)
    new_subdomain_name: Mapped[str] = mapped_column(String(63), nullable=False)
    old_full_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    new_full_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    # Relationship
    rental: Mapped["Rental"] = relationship("Rental", back_populates="name_history")

    def __repr__(self) -> str:
        return f"<RentalNameHistory {self.old_full_domain} -> {self.new_full_domain}>"

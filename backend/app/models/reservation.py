"""
Name reservation model — temporary checkout reservations.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NameReservation(Base):
    """
    Temporary reservation during checkout to prevent concurrent purchases.
    Expires automatically after CHECKOUT_RESERVATION_MINUTES.
    """

    __tablename__ = "name_reservations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    parent_domain_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("parent_domains.id", ondelete="CASCADE"),
        nullable=False,
    )
    subdomain_name: Mapped[str] = mapped_column(
        String(63), nullable=False
    )

    # Reservation expiry
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index(
            "uq_active_reservation",
            "parent_domain_id", "subdomain_name",
            unique=True,
        ),
    )

    @property
    def is_expired(self) -> bool:
        return datetime.now(tz=self.expires_at.tzinfo) > self.expires_at

    def __repr__(self) -> str:
        return f"<NameReservation {self.subdomain_name} user={self.user_id}>"

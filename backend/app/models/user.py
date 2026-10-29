"""
User and Admin models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """Customer user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    suspension_reason: Mapped[str | None] = mapped_column(Text)

    # Email verification
    email_verification_token: Mapped[str | None] = mapped_column(String(512))
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Password reset
    password_reset_token: Mapped[str | None] = mapped_column(String(512))
    password_reset_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Notification preferences
    notify_expiry_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_wallet_events: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_low_balance: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    wallet: Mapped["Wallet"] = relationship(
        "Wallet", back_populates="user", uselist=False, lazy="selectin"
    )
    rentals: Mapped[list["Rental"]] = relationship(
        "Rental", back_populates="user", lazy="selectin"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class AdminUser(Base):
    """Administrative user account (separate from customer accounts)."""

    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))

    # Role-based access
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, default="admin"
    )  # "super_admin", "admin", "support"

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # MFA
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(255))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<AdminUser {self.email} role={self.role}>"

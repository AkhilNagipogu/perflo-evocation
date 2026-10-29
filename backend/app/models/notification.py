"""
Notification model.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Notification(Base):
    """In-app notification for a user."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # Notification category
    category: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # "expiry_reminder", "wallet", "rental", "security", "abuse", etc.

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Link to relevant resource
    action_url: Mapped[str | None] = mapped_column(String(512))
    action_label: Mapped[str | None] = mapped_column(String(64))

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_unread", "user_id", "is_read"),
    )

    def __repr__(self) -> str:
        return f"<Notification {self.category} user={self.user_id}>"

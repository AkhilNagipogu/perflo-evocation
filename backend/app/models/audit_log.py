"""
Audit log model — immutable record of significant operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    """Immutable audit log entry."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )

    # Who performed the action
    actor_type: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # "user", "admin", "system"
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    actor_email: Mapped[str | None] = mapped_column(String(255))
    actor_ip: Mapped[str | None] = mapped_column(String(45))

    # What happened
    action: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    resource_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "user", "rental", "wallet", "dns_record", etc.
    resource_id: Mapped[str | None] = mapped_column(String(128))

    # Details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details_before: Mapped[str | None] = mapped_column(Text)  # JSON
    details_after: Mapped[str | None] = mapped_column(Text)  # JSON
    metadata_json: Mapped[str | None] = mapped_column(Text)  # JSON extra context

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_audit_logs_actor", "actor_type", "actor_id"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.resource_type}:{self.resource_id}>"

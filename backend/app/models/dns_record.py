"""
DNS record model — tracks records managed through Cloudflare.
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DnsRecordType(str, enum.Enum):
    """Supported DNS record types."""
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    TXT = "TXT"


class DnsRecordStatus(str, enum.Enum):
    """DNS record synchronization status."""
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    SUSPENDED = "suspended"
    DELETING = "deleting"
    DELETED = "deleted"


class DnsRecord(Base):
    """A DNS record associated with a rental."""

    __tablename__ = "dns_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    rental_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("rentals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    record_type: Mapped[DnsRecordType] = mapped_column(
        SAEnum(DnsRecordType), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String(4096), nullable=False)
    ttl: Mapped[int] = mapped_column(Integer, default=3600)  # seconds
    proxied: Mapped[bool] = mapped_column(default=False)

    # Cloudflare reference
    cloudflare_record_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, index=True
    )

    status: Mapped[DnsRecordStatus] = mapped_column(
        SAEnum(DnsRecordStatus), nullable=False, default=DnsRecordStatus.PENDING
    )

    # Error tracking
    last_error: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    rental: Mapped["Rental"] = relationship("Rental", back_populates="dns_records")

    __table_args__ = (
        Index("ix_dns_records_rental_type", "rental_id", "record_type"),
    )

    def __repr__(self) -> str:
        return f"<DnsRecord {self.record_type.value} {self.name} -> {self.content}>"

"""
Parent domain model — configurable DNS zones managed by the platform.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ParentDomain(Base):
    """A parent domain under which subdomains are rented."""

    __tablename__ = "parent_domains"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    domain: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    cloudflare_zone_id: Mapped[str] = mapped_column(
        String(64), nullable=False, default=""
    )
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Reserved names that cannot be rented (comma-separated or JSON)
    reserved_names: Mapped[str | None] = mapped_column(
        Text, default="www,mail,ftp,admin,api,ns1,ns2,mx,smtp,imap,pop,webmail,cpanel,whm,autodiscover,autoconfig,_dmarc,_domainkey"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    rentals: Mapped[list["Rental"]] = relationship(
        "Rental", back_populates="parent_domain", lazy="noload"
    )

    @property
    def reserved_name_list(self) -> list[str]:
        """Parse reserved names into a list."""
        if not self.reserved_names:
            return []
        return [n.strip().lower() for n in self.reserved_names.split(",") if n.strip()]

    def __repr__(self) -> str:
        return f"<ParentDomain {self.domain}>"

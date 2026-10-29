"""
System configuration model — admin-managed key-value settings.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SystemConfig(Base):
    """Admin-configurable system settings stored in the database."""

    __tablename__ = "system_config"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    value_type: Mapped[str] = mapped_column(
        String(16), default="string"
    )  # "string", "integer", "boolean", "json"

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    updated_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    def __repr__(self) -> str:
        return f"<SystemConfig {self.key}={self.value[:50]}>"

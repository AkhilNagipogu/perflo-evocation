"""
Abuse report and enforcement action models.
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
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AbuseCategory(str, enum.Enum):
    """Categories of abuse reports."""
    PHISHING = "phishing"
    MALWARE = "malware"
    IMPERSONATION = "impersonation"
    SPAM = "spam"
    ILLEGAL_CONTENT = "illegal_content"
    TRADEMARK = "trademark"
    OTHER = "other"


class AbuseReportStatus(str, enum.Enum):
    """Abuse report workflow status."""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    ACTION_TAKEN = "action_taken"


class AbuseReport(Base):
    """Public abuse report submission."""

    __tablename__ = "abuse_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    reference_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )

    # Reported subdomain
    reported_domain: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    category: Mapped[AbuseCategory] = mapped_column(
        SAEnum(AbuseCategory), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_urls: Mapped[str | None] = mapped_column(Text)  # JSON array

    # Reporter info
    reporter_email: Mapped[str | None] = mapped_column(String(255))
    reporter_name: Mapped[str | None] = mapped_column(String(255))

    # Status
    status: Mapped[AbuseReportStatus] = mapped_column(
        SAEnum(AbuseReportStatus), nullable=False, default=AbuseReportStatus.SUBMITTED
    )

    # Linked rental (if identified)
    rental_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("rentals.id", ondelete="SET NULL"), nullable=True
    )

    # Review
    reviewed_by_admin_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_abuse_reports_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<AbuseReport {self.reference_id} {self.reported_domain}>"


class AbuseAction(Base):
    """Record of enforcement action taken on an abuse report."""

    __tablename__ = "abuse_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    abuse_report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("abuse_reports.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("admin_users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    action_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # "suspend_rental", "ban_user", "dismiss", "restore"
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Before/after state
    state_before: Mapped[str | None] = mapped_column(Text)  # JSON
    state_after: Mapped[str | None] = mapped_column(Text)  # JSON

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<AbuseAction {self.action_type} report={self.abuse_report_id}>"

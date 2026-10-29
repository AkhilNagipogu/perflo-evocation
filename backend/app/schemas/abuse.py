"""
Abuse report schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class AbuseReportCreate(BaseModel):
    """Public abuse report submission."""
    reported_domain: str = Field(min_length=3, max_length=255)
    category: str  # AbuseCategory values
    description: str = Field(min_length=20, max_length=5000)
    evidence_urls: Optional[list[str]] = None
    reporter_email: Optional[EmailStr] = None
    reporter_name: Optional[str] = Field(None, max_length=255)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        valid = {"phishing", "malware", "impersonation", "spam", "illegal_content", "trademark", "other"}
        if v not in valid:
            raise ValueError(f"Category must be one of: {', '.join(valid)}")
        return v


class AbuseReportResponse(BaseModel):
    """Abuse report response."""
    id: uuid.UUID
    reference_id: str
    reported_domain: str
    category: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AbuseReportDetailResponse(AbuseReportResponse):
    """Detailed abuse report (admin view)."""
    description: str
    evidence_urls: Optional[str] = None
    reporter_email: Optional[str] = None
    reporter_name: Optional[str] = None
    rental_id: Optional[uuid.UUID] = None
    reviewed_by_admin_id: Optional[uuid.UUID] = None
    review_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    updated_at: datetime


class AbuseReportReview(BaseModel):
    """Admin review of an abuse report."""
    status: str  # "under_review", "confirmed", "dismissed", "action_taken"
    review_notes: str = Field(min_length=5, max_length=5000)
    action_type: Optional[str] = None  # "suspend_rental", "ban_user", "dismiss", "restore"


class PricingPlanResponse(BaseModel):
    """Pricing plan response."""
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    price_paise: int
    price_display: str
    included_subdomains: int
    billing_period_days: int
    is_active: bool
    is_base_plan: bool

    model_config = {"from_attributes": True}


class ParentDomainResponse(BaseModel):
    """Parent domain response."""
    id: uuid.UUID
    domain: str
    description: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class NotificationResponse(BaseModel):
    """Notification response."""
    id: uuid.UUID
    category: str
    title: str
    message: str
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int

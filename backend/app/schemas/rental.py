"""
Rental and subdomain schemas.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SubdomainSearchRequest(BaseModel):
    """Search for subdomain availability."""
    subdomain_name: str = Field(min_length=1, max_length=63)
    parent_domain_id: uuid.UUID

    @field_validator("subdomain_name")
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", v):
            raise ValueError(
                "Subdomain must start and end with a letter or digit, "
                "and may contain hyphens"
            )
        if len(v) < 2:
            raise ValueError("Subdomain must be at least 2 characters")
        if "--" in v:
            raise ValueError("Subdomain cannot contain consecutive hyphens")
        return v


class SubdomainAvailabilityResponse(BaseModel):
    """Availability check result."""
    subdomain_name: str
    parent_domain: str
    full_domain: str
    is_available: bool
    reason: Optional[str] = None  # "active_rental", "reserved", "grace_period", "prohibited", "dns_conflict"
    message: Optional[str] = None
    price_paise: Optional[int] = None
    price_display: Optional[str] = None
    plan_name: Optional[str] = None
    billing_period_days: Optional[int] = None


class RentalPurchaseRequest(BaseModel):
    """Purchase a subdomain rental."""
    subdomain_name: str = Field(min_length=2, max_length=63)
    parent_domain_id: uuid.UUID
    pricing_plan_id: uuid.UUID
    coupon_code: Optional[str] = None
    auto_renew: bool = False

    @field_validator("subdomain_name")
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        return v.strip().lower()


class RentalResponse(BaseModel):
    """Rental details."""
    id: uuid.UUID
    subdomain_name: str
    parent_domain: str
    full_domain: str
    status: str
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    grace_period_ends_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    price_paid_paise: int
    auto_renew: bool
    rename_count: int
    last_renamed_at: Optional[datetime] = None
    created_at: datetime
    dns_records: list["DnsRecordResponse"] = []

    model_config = {"from_attributes": True}


class RentalListResponse(BaseModel):
    """List of rentals."""
    items: list[RentalResponse]
    total: int


class RenameRequest(BaseModel):
    """Rename a subdomain."""
    new_subdomain_name: str = Field(min_length=2, max_length=63)

    @field_validator("new_subdomain_name")
    @classmethod
    def validate_subdomain(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", v):
            raise ValueError(
                "Subdomain must start and end with a letter or digit, "
                "and may contain hyphens"
            )
        return v


class RenewRequest(BaseModel):
    """Renew a rental subscription."""
    coupon_code: Optional[str] = None


class DnsRecordCreate(BaseModel):
    """Create a DNS record."""
    record_type: str = Field(pattern=r"^(A|AAAA|CNAME|TXT)$")
    content: str = Field(min_length=1, max_length=4096)
    ttl: int = Field(default=3600, ge=60, le=86400)
    proxied: bool = False

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        return v.strip()


class DnsRecordUpdate(BaseModel):
    """Update a DNS record."""
    content: Optional[str] = Field(None, min_length=1, max_length=4096)
    ttl: Optional[int] = Field(None, ge=60, le=86400)
    proxied: Optional[bool] = None


class DnsRecordResponse(BaseModel):
    """DNS record response."""
    id: uuid.UUID
    record_type: str
    name: str
    content: str
    ttl: int
    proxied: bool
    status: str
    last_synced_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}

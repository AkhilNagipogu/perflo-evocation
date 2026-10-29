"""
Admin-related schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class AdminLoginRequest(BaseModel):
    """Admin login."""
    email: EmailStr
    password: str


class AdminUserResponse(BaseModel):
    """Admin user profile."""
    id: uuid.UUID
    email: str
    username: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    mfa_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AdminDashboardStats(BaseModel):
    """Admin overview statistics."""
    total_users: int
    active_users: int
    total_rentals: int
    active_rentals: int
    expiring_soon: int  # Expiring within 7 days
    in_grace_period: int
    released_this_month: int
    total_wallet_balance_paise: int
    payments_this_month_paise: int
    failed_dns_operations: int
    pending_abuse_reports: int
    active_coupons: int


class AdminUserManageRequest(BaseModel):
    """Admin managing a user account."""
    action: str  # "suspend", "unsuspend", "verify_email"
    reason: Optional[str] = None


class AdminRentalManageRequest(BaseModel):
    """Admin managing a rental."""
    action: str  # "extend", "suspend", "release", "restore"
    extend_days: Optional[int] = None
    reason: str


class AdminWalletAdjustment(BaseModel):
    """Admin wallet adjustment."""
    amount_paise: int  # Positive for credit, negative for debit
    reason: str = Field(min_length=10, max_length=500)
    reference: Optional[str] = None


class AdminRefundRequest(BaseModel):
    """Admin refund."""
    transaction_id: uuid.UUID
    amount_paise: int = Field(gt=0)
    reason: str = Field(min_length=10, max_length=500)


class SystemConfigUpdate(BaseModel):
    """Update a system config entry."""
    value: str
    description: Optional[str] = None

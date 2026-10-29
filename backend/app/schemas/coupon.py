"""
Coupon schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CouponCreate(BaseModel):
    """Create a coupon (admin only)."""
    code: str = Field(min_length=3, max_length=64)
    description: Optional[str] = None
    discount_type: str  # "percentage" or "fixed"
    discount_value: int = Field(gt=0)
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, gt=0)
    max_uses_per_user: int = Field(default=1, gt=0)
    min_purchase_paise: int = Field(default=0, ge=0)
    eligible_plans: Optional[str] = None  # JSON array of plan slugs

    @field_validator("discount_type")
    @classmethod
    def validate_discount_type(cls, v: str) -> str:
        if v not in ("percentage", "fixed"):
            raise ValueError("discount_type must be 'percentage' or 'fixed'")
        return v

    @field_validator("code")
    @classmethod
    def normalize_code(cls, v: str) -> str:
        return v.strip().upper()


class CouponUpdate(BaseModel):
    """Update a coupon (admin only)."""
    description: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    max_uses_per_user: Optional[int] = None
    min_purchase_paise: Optional[int] = None
    eligible_plans: Optional[str] = None


class CouponResponse(BaseModel):
    """Coupon details."""
    id: uuid.UUID
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: int
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    max_uses: Optional[int] = None
    max_uses_per_user: int
    current_uses: int
    min_purchase_paise: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CouponValidateRequest(BaseModel):
    """Validate a coupon for a purchase."""
    code: str
    plan_id: uuid.UUID
    amount_paise: int = Field(gt=0)


class CouponValidateResponse(BaseModel):
    """Coupon validation result."""
    is_valid: bool
    code: str
    discount_type: Optional[str] = None
    discount_value: Optional[int] = None
    discount_amount_paise: Optional[int] = None
    final_amount_paise: Optional[int] = None
    reason: Optional[str] = None

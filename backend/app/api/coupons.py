"""
Coupon validation and management API routes.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_user
from app.models.admin_user import AdminUser
from app.models.user import User
from app.schemas.coupon import (
    CouponCreate,
    CouponResponse,
    CouponUpdate,
    CouponValidateRequest,
    CouponValidateResponse,
)
from app.services.coupon_service import CouponService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Coupons"])


@router.post("/coupons/validate", response_model=CouponValidateResponse)
async def validate_coupon(
    data: CouponValidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Validate a promotional coupon code for an impending purchase."""
    coupon_service = CouponService(db)
    result = await coupon_service.validate_coupon(
        code=data.code,
        user_id=current_user.id,
        amount_paise=data.amount_paise,
        plan_id=data.plan_id,
    )
    return result


# Admin routes for coupon management
@router.post("/admin/coupons", response_model=CouponResponse, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    data: CouponCreate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new promotional discount coupon (Admin only)."""
    coupon_service = CouponService(db)
    try:
        coupon = await coupon_service.create_coupon(data, admin_id=current_admin.id)
        await db.commit()
        await db.refresh(coupon)
        return coupon
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/admin/coupons", response_model=list[CouponResponse])
async def list_coupons(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    active_only: bool = Query(False),
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List coupons with usage counters and validity filters (Admin only)."""
    coupon_service = CouponService(db)
    coupons, _ = await coupon_service.list_coupons(skip=skip, limit=limit, active_only=active_only)
    return coupons


@router.patch("/admin/coupons/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: uuid.UUID,
    data: CouponUpdate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update coupon properties or de-activate an active coupon (Admin only)."""
    coupon_service = CouponService(db)
    try:
        updated = await coupon_service.update_coupon(coupon_id, data)
        await db.commit()
        return updated
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

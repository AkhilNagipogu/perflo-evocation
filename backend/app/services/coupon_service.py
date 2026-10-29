"""
Coupon service — validates coupons, computes discounts, and tracks redemptions.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coupon import Coupon, CouponRedemption
from app.models.pricing import PricingPlan
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponValidateResponse


class CouponService:
    """Service for managing discount coupons and processing redemptions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_code(self, code: str) -> Optional[Coupon]:
        """Fetch coupon by its code (case-insensitive)."""
        clean_code = code.strip().upper()
        stmt = select(Coupon).where(func.upper(Coupon.code) == clean_code)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, coupon_id: uuid.UUID) -> Optional[Coupon]:
        """Fetch coupon by primary key ID."""
        stmt = select(Coupon).where(Coupon.id == coupon_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def validate_coupon(
        self,
        code: str,
        user_id: uuid.UUID,
        amount_paise: int,
        plan_id: Optional[uuid.UUID] = None,
    ) -> CouponValidateResponse:
        """
        Validate whether a coupon can be applied to a specific purchase.
        Returns a CouponValidateResponse with discount details or failure reason.
        """
        coupon = await self.get_by_code(code)
        if not coupon:
            return CouponValidateResponse(
                is_valid=False,
                code=code,
                reason="Coupon code not found",
            )

        now = datetime.now(timezone.utc)

        if not coupon.is_active:
            return CouponValidateResponse(
                is_valid=False,
                code=code,
                reason="This coupon is no longer active",
            )

        starts_at = (
            coupon.starts_at.replace(tzinfo=timezone.utc)
            if (coupon.starts_at and coupon.starts_at.tzinfo is None)
            else coupon.starts_at
        )
        expires_at = (
            coupon.expires_at.replace(tzinfo=timezone.utc)
            if (coupon.expires_at and coupon.expires_at.tzinfo is None)
            else coupon.expires_at
        )

        if starts_at and starts_at > now:
            return CouponValidateResponse(
                is_valid=False,
                code=code,
                reason="This coupon is not yet active",
            )

        if expires_at and expires_at < now:
            return CouponValidateResponse(
                is_valid=False,
                code=code,
                reason="This coupon has expired",
            )

        if coupon.max_uses is not None and coupon.current_uses >= coupon.max_uses:
            return CouponValidateResponse(
                is_valid=False,
                code=code,
                reason="This coupon has reached its maximum total uses",
            )

        # Check user-specific redemption limit
        user_redemptions_stmt = select(func.count(CouponRedemption.id)).where(
            CouponRedemption.coupon_id == coupon.id,
            CouponRedemption.user_id == user_id,
        )
        user_redemptions_res = await self.db.execute(user_redemptions_stmt)
        user_redemptions = user_redemptions_res.scalar_one()

        if user_redemptions >= coupon.max_uses_per_user:
            return CouponValidateResponse(
                is_valid=False,
                code=code,
                reason="You have already redeemed this coupon the maximum allowed times",
            )

        if amount_paise < coupon.min_purchase_paise:
            min_rs = coupon.min_purchase_paise / 100
            return CouponValidateResponse(
                is_valid=False,
                code=code,
                reason=f"Minimum purchase of ₹{min_rs:.2f} required for this coupon",
            )

        # Check plan eligibility if specified
        if coupon.eligible_plans and plan_id:
            try:
                allowed_plans = json.loads(coupon.eligible_plans)
                if isinstance(allowed_plans, list) and allowed_plans:
                    plan_stmt = select(PricingPlan).where(PricingPlan.id == plan_id)
                    plan_res = await self.db.execute(plan_stmt)
                    plan = plan_res.scalars().first()
                    if plan and plan.slug not in allowed_plans and str(plan.id) not in allowed_plans:
                        return CouponValidateResponse(
                            is_valid=False,
                            code=code,
                            reason="This coupon is not applicable to the selected plan",
                        )
            except Exception:
                pass

        # Calculate discount
        if coupon.discount_type == "percentage":
            discount_paise = (amount_paise * coupon.discount_value) // 100
        else:  # "fixed"
            discount_paise = coupon.discount_value

        # Cap discount at the total purchase amount
        discount_paise = max(0, min(discount_paise, amount_paise))
        final_amount_paise = max(0, amount_paise - discount_paise)

        return CouponValidateResponse(
            is_valid=True,
            code=coupon.code,
            discount_type=coupon.discount_type,
            discount_value=coupon.discount_value,
            discount_amount_paise=discount_paise,
            final_amount_paise=final_amount_paise,
        )

    async def redeem_coupon(
        self,
        coupon_id: uuid.UUID,
        user_id: uuid.UUID,
        discount_amount_paise: int,
        rental_id: Optional[uuid.UUID] = None,
        subscription_id: Optional[uuid.UUID] = None,
    ) -> CouponRedemption:
        """
        Record a coupon redemption and increment current_uses on the coupon.
        Must be called within an active database transaction.
        """
        coupon = await self.get_by_id(coupon_id)
        if not coupon:
            raise ValueError(f"Coupon {coupon_id} not found")

        coupon.current_uses += 1

        redemption = CouponRedemption(
            coupon_id=coupon.id,
            user_id=user_id,
            rental_id=rental_id,
            subscription_id=subscription_id,
            discount_amount_paise=discount_amount_paise,
        )
        self.db.add(redemption)
        await self.db.flush()
        return redemption

    # Admin operations
    async def create_coupon(
        self,
        data: CouponCreate,
        admin_id: Optional[uuid.UUID] = None,
    ) -> Coupon:
        """Create a new coupon."""
        existing = await self.get_by_code(data.code)
        if existing:
            raise ValueError(f"Coupon code '{data.code}' already exists")

        coupon = Coupon(
            code=data.code.strip().upper(),
            description=data.description,
            discount_type=data.discount_type,
            discount_value=data.discount_value,
            starts_at=data.starts_at,
            expires_at=data.expires_at,
            is_active=True,
            max_uses=data.max_uses,
            max_uses_per_user=data.max_uses_per_user,
            min_purchase_paise=data.min_purchase_paise,
            eligible_plans=data.eligible_plans,
            created_by_admin_id=admin_id,
        )
        self.db.add(coupon)
        await self.db.flush()
        await self.db.refresh(coupon)
        return coupon

    async def update_coupon(
        self,
        coupon_id: uuid.UUID,
        data: CouponUpdate,
    ) -> Coupon:
        """Update an existing coupon."""
        coupon = await self.get_by_id(coupon_id)
        if not coupon:
            raise ValueError("Coupon not found")

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(coupon, key, value)

        await self.db.flush()
        await self.db.refresh(coupon)
        return coupon

    async def list_coupons(
        self,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = False,
    ) -> tuple[list[Coupon], int]:
        """List coupons with pagination."""
        stmt = select(Coupon)
        if active_only:
            stmt = stmt.where(Coupon.is_active.is_(True))

        count_stmt = select(func.count(Coupon.id))
        if active_only:
            count_stmt = count_stmt.where(Coupon.is_active.is_(True))

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(Coupon.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        coupons = list(result.scalars().all())

        return coupons, total

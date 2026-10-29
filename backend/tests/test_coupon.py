"""
Tests for discount coupons: percentage, fixed amount, expiry, and usage limits.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.coupon import CouponCreate
from app.services.coupon_service import CouponService


@pytest.mark.asyncio
async def test_percentage_coupon_validation(db_session: AsyncSession, test_user):
    """Test 10% coupon validation on ₹60 (6000 paise) purchase."""
    service = CouponService(db_session)
    await service.create_coupon(
        CouponCreate(
            code="SAVE10",
            discount_type="percentage",
            discount_value=10,
        )
    )

    result = await service.validate_coupon(
        code="SAVE10",
        user_id=test_user.id,
        amount_paise=6000,
    )
    assert result.is_valid is True
    assert result.discount_amount_paise == 600  # 10% of 6000 = 600 paise (₹6)
    assert result.final_amount_paise == 5400  # ₹54


@pytest.mark.asyncio
async def test_expired_coupon_validation(db_session: AsyncSession, test_user):
    """Expired coupon must fail validation."""
    service = CouponService(db_session)
    past_date = datetime.now(timezone.utc) - timedelta(days=2)
    await service.create_coupon(
        CouponCreate(
            code="EXPIRED",
            discount_type="fixed",
            discount_value=1000,
            expires_at=past_date,
        )
    )

    result = await service.validate_coupon(
        code="EXPIRED",
        user_id=test_user.id,
        amount_paise=6000,
    )
    assert result.is_valid is False
    assert "expired" in result.reason.lower()


@pytest.mark.asyncio
async def test_coupon_max_uses_per_user(db_session: AsyncSession, test_user):
    """Coupon with max_uses_per_user=1 cannot be redeemed twice by same user."""
    service = CouponService(db_session)
    coupon = await service.create_coupon(
        CouponCreate(
            code="ONCEONLY",
            discount_type="fixed",
            discount_value=500,
            max_uses_per_user=1,
        )
    )

    # First validation is valid
    res1 = await service.validate_coupon("ONCEONLY", test_user.id, 6000)
    assert res1.is_valid is True

    # Redeem it
    await service.redeem_coupon(coupon.id, test_user.id, 500)

    # Second validation must fail
    res2 = await service.validate_coupon("ONCEONLY", test_user.id, 6000)
    assert res2.is_valid is False
    assert "maximum allowed" in res2.reason.lower()

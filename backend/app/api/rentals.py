"""
Subdomain search, purchase, lifecycle, and management API routes.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_verified_user
from app.models.parent_domain import ParentDomain
from app.models.rental import Rental
from app.models.user import User
from app.schemas.rental import (
    RentalListResponse,
    RentalPurchaseRequest,
    RentalResponse,
    RenameRequest,
    RenewRequest,
    SubdomainAvailabilityResponse,
    SubdomainSearchRequest,
)
from app.services.coupon_service import CouponService
from app.services.rental_service import RentalService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/rentals", tags=["Rentals"])


def _to_rental_response(rental: Rental) -> RentalResponse:
    """Format Rental model into response schema with days_remaining calculation."""
    return RentalResponse(
        id=rental.id,
        subdomain_name=rental.subdomain_name,
        parent_domain=rental.parent_domain.domain if rental.parent_domain else "",
        full_domain=rental.full_domain,
        status=rental.status.value,
        started_at=rental.started_at,
        expires_at=rental.expires_at,
        grace_period_ends_at=rental.grace_period_ends_at,
        days_remaining=rental.days_remaining if hasattr(rental, "days_remaining") else None,
        price_paid_paise=rental.price_paid_paise,
        auto_renew=rental.auto_renew,
        rename_count=rental.rename_count,
        last_renamed_at=rental.last_renamed_at,
        created_at=rental.created_at,
        dns_records=[
            {
                "id": r.id,
                "record_type": r.record_type.value,
                "name": r.name,
                "content": r.content,
                "ttl": r.ttl,
                "proxied": r.proxied,
                "status": r.status.value,
                "last_synced_at": r.last_synced_at,
            }
            for r in (rental.dns_records or [])
        ],
    )


@router.post("/search", response_model=SubdomainAvailabilityResponse)
async def check_availability(
    data: SubdomainSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Public search endpoint to check subdomain availability across 6 validation layers."""
    service = RentalService(db)
    result = await service.check_availability(
        subdomain_name=data.subdomain_name,
        parent_domain_id=data.parent_domain_id,
    )
    return SubdomainAvailabilityResponse(**result)


@router.post("/purchase", response_model=RentalResponse, status_code=status.HTTP_201_CREATED)
async def purchase_rental(
    data: RentalPurchaseRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Purchase a subdomain rental from wallet balance with optional coupon code."""
    service = RentalService(db)
    coupon_service = CouponService(db)

    coupon_discount_paise = 0
    coupon_id = None

    if data.coupon_code:
        # Fetch plan price to validate discount
        res = await db.execute(
            select(ParentDomain).where(ParentDomain.id == data.parent_domain_id)
        )
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent domain not found")

        validation = await coupon_service.validate_coupon(
            code=data.coupon_code,
            user_id=current_user.id,
            amount_paise=6000,  # Base bundle price: ₹60
            plan_id=data.pricing_plan_id,
        )
        if not validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid coupon: {validation.reason}",
            )
        coupon_discount_paise = validation.discount_amount_paise or 0
        coupon = await coupon_service.get_by_code(data.coupon_code)
        if coupon:
            coupon_id = coupon.id

    try:
        rental = await service.purchase_rental(
            user_id=current_user.id,
            subdomain_name=data.subdomain_name,
            parent_domain_id=data.parent_domain_id,
            pricing_plan_id=data.pricing_plan_id,
            coupon_discount_paise=coupon_discount_paise,
            coupon_id=coupon_id,
            auto_renew=data.auto_renew,
        )

        if coupon_id and coupon_discount_paise > 0:
            await coupon_service.redeem_coupon(
                coupon_id=coupon_id,
                user_id=current_user.id,
                discount_amount_paise=coupon_discount_paise,
                rental_id=rental.id,
            )

        await db.commit()
        # Reload relationships
        stmt = (
            select(Rental)
            .where(Rental.id == rental.id)
            .options(selectinload(Rental.parent_domain), selectinload(Rental.dns_records))
        )
        reloaded = (await db.execute(stmt)).scalar_one()
        return _to_rental_response(reloaded)

    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my-rentals", response_model=RentalListResponse)
async def list_my_rentals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve all active, expired, or grace-period rentals owned by current customer."""
    stmt = (
        select(Rental)
        .where(
            Rental.user_id == current_user.id,
            Rental.status.notin_(["released", "cancelled"]),
        )
        .options(selectinload(Rental.parent_domain), selectinload(Rental.dns_records))
        .order_by(Rental.created_at.desc())
    )
    res = await db.execute(stmt)
    rentals = list(res.scalars().all())
    items = [_to_rental_response(r) for r in rentals]
    return RentalListResponse(items=items, total=len(items))


@router.get("/{rental_id}", response_model=RentalResponse)
async def get_rental(
    rental_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get details of a specific rental owned by current customer."""
    stmt = (
        select(Rental)
        .where(Rental.id == rental_id, Rental.user_id == current_user.id)
        .options(selectinload(Rental.parent_domain), selectinload(Rental.dns_records))
    )
    res = await db.execute(stmt)
    rental = res.scalar_one_or_none()
    if not rental:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rental not found")
    return _to_rental_response(rental)


@router.post("/{rental_id}/rename", response_model=RentalResponse)
async def rename_rental(
    rental_id: uuid.UUID,
    data: RenameRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Rename an active subdomain.
    Preserves expiration dates, enforces 24-hour rename cooldown, records audit history.
    """
    service = RentalService(db)
    try:
        rental = await service.rename_rental(
            rental_id=rental_id,
            user_id=current_user.id,
            new_subdomain_name=data.new_subdomain_name,
        )
        await db.commit()

        stmt = (
            select(Rental)
            .where(Rental.id == rental.id)
            .options(selectinload(Rental.parent_domain), selectinload(Rental.dns_records))
        )
        reloaded = (await db.execute(stmt)).scalar_one()
        return _to_rental_response(reloaded)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{rental_id}/renew", response_model=RentalResponse)
async def renew_rental(
    rental_id: uuid.UUID,
    data: RenewRequest,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    Renew a subdomain rental subscription.
    Debits wallet and extends expiration date from existing expiry date.
    """
    service = RentalService(db)
    coupon_service = CouponService(db)

    coupon_discount_paise = 0
    if data.coupon_code:
        validation = await coupon_service.validate_coupon(
            code=data.coupon_code,
            user_id=current_user.id,
            amount_paise=6000,
        )
        if not validation.is_valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=validation.reason)
        coupon_discount_paise = validation.discount_amount_paise or 0

    try:
        rental = await service.renew_rental(
            rental_id=rental_id,
            user_id=current_user.id,
            coupon_discount_paise=coupon_discount_paise,
        )
        await db.commit()

        stmt = (
            select(Rental)
            .where(Rental.id == rental.id)
            .options(selectinload(Rental.parent_domain), selectinload(Rental.dns_records))
        )
        reloaded = (await db.execute(stmt)).scalar_one()
        return _to_rental_response(reloaded)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{rental_id}/auto-renew", response_model=RentalResponse)
async def toggle_auto_renew(
    rental_id: uuid.UUID,
    auto_renew: bool = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Enable or disable auto-renewal for a rental."""
    service = RentalService(db)
    try:
        rental = await service.set_auto_renew(
            rental_id=rental_id,
            user_id=current_user.id,
            auto_renew=auto_renew,
        )
        await db.commit()

        stmt = (
            select(Rental)
            .where(Rental.id == rental.id)
            .options(selectinload(Rental.parent_domain), selectinload(Rental.dns_records))
        )
        reloaded = (await db.execute(stmt)).scalar_one()
        return _to_rental_response(reloaded)
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

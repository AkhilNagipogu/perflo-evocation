"""
Public pricing plans and parent domains API routes.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.parent_domain import ParentDomain
from app.models.pricing import PricingPlan
from app.schemas.abuse import ParentDomainResponse, PricingPlanResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pricing", tags=["Pricing & Domains"])


@router.get("/plans", response_model=list[PricingPlanResponse])
async def list_pricing_plans(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Public list of active subscription plans and pricing."""
    stmt = (
        select(PricingPlan)
        .where(PricingPlan.is_active.is_(True))
        .order_by(PricingPlan.price_paise.asc())
    )
    res = await db.execute(stmt)
    plans = list(res.scalars().all())
    return [
        PricingPlanResponse(
            id=p.id,
            name=p.name,
            slug=p.slug,
            description=p.description,
            price_paise=p.price_paise,
            price_display=f"₹{p.price_paise / 100:.2f}",
            included_subdomains=p.included_subdomains,
            billing_period_days=p.billing_period_days,
            is_active=p.is_active,
            is_base_plan=p.is_base_plan,
        )
        for p in plans
    ]


@router.get("/domains", response_model=list[ParentDomainResponse])
async def list_parent_domains(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Public list of active root domains available for subdomain selection."""
    stmt = (
        select(ParentDomain)
        .where(ParentDomain.is_active.is_(True))
        .order_by(ParentDomain.domain.asc())
    )
    res = await db.execute(stmt)
    domains = list(res.scalars().all())
    return [
        ParentDomainResponse(
            id=d.id,
            domain=d.domain,
            description=d.description,
            is_active=d.is_active,
        )
        for d in domains
    ]

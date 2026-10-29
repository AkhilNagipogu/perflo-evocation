"""
Administrative control panel API routes.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models.admin_user import AdminUser
from app.models.rental import Rental
from app.models.system_config import SystemConfig
from app.models.user import User
from app.schemas.admin import (
    AdminDashboardStats,
    AdminLoginRequest,
    AdminRefundRequest,
    AdminRentalManageRequest,
    AdminUserManageRequest,
    AdminUserResponse,
    AdminWalletAdjustment,
    SystemConfigUpdate,
)
from app.schemas.rental import RentalResponse
from app.schemas.user import TokenResponse, UserResponse
from app.services.admin_service import AdminService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/login", response_model=TokenResponse)
async def admin_login(
    data: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Administrator authentication returning admin-scoped JWT."""
    stmt = select(AdminUser).where(AdminUser.email == data.email)
    res = await db.execute(stmt)
    admin = res.scalars().first()

    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrative credentials",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative account is disabled",
        )

    admin.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    token_data = {"sub": str(admin.id), "is_admin": True, "role": admin.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=60 * 60,
    )


@router.get("/me", response_model=AdminUserResponse)
async def get_admin_me(
    current_admin: AdminUser = Depends(get_current_admin),
) -> Any:
    """Get authenticated administrator profile."""
    return current_admin


@router.get("/stats", response_model=AdminDashboardStats)
async def get_stats(
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Aggregate high-level system, financial, and operational metrics."""
    service = AdminService(db)
    return await service.get_dashboard_stats()


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List registered customers with search filtering."""
    stmt = select(User)
    if search:
        pattern = f"%{search.strip().lower()}%"
        stmt = stmt.where((User.email.ilike(pattern)) | (User.username.ilike(pattern)))

    stmt = stmt.order_by(User.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("/users/{user_id}/manage", response_model=UserResponse)
async def manage_user(
    user_id: uuid.UUID,
    data: AdminUserManageRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Perform suspension, un-suspension, or manual email verification on a user."""
    service = AdminService(db)
    try:
        user = await service.manage_user(
            user_id=user_id,
            action=data.action,
            admin_id=current_admin.id,
            reason=data.reason,
        )
        await db.commit()
        return user
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/rentals")
async def list_rentals(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all subdomain rentals across the platform."""
    stmt = select(Rental).options(selectinload(Rental.parent_domain), selectinload(Rental.dns_records))
    if status_filter:
        stmt = stmt.where(Rental.status == status_filter)
    if search:
        stmt = stmt.where(Rental.full_domain.ilike(f"%{search.strip().lower()}%"))

    stmt = stmt.order_by(Rental.created_at.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    rentals = list(res.scalars().all())

    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "subdomain_name": r.subdomain_name,
            "parent_domain": r.parent_domain.domain if r.parent_domain else "",
            "full_domain": r.full_domain,
            "status": r.status.value,
            "expires_at": r.expires_at,
            "grace_period_ends_at": r.grace_period_ends_at,
            "auto_renew": r.auto_renew,
            "created_at": r.created_at,
        }
        for r in rentals
    ]


@router.post("/rentals/{rental_id}/manage")
async def manage_rental(
    rental_id: uuid.UUID,
    data: AdminRentalManageRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Suspend, restore, release, or extend an active or expired rental."""
    service = AdminService(db)
    try:
        rental = await service.manage_rental(
            rental_id=rental_id,
            action=data.action,
            admin_id=current_admin.id,
            reason=data.reason,
            extend_days=data.extend_days,
        )
        await db.commit()
        return {
            "id": str(rental.id),
            "status": rental.status.value,
            "expires_at": rental.expires_at.isoformat() if rental.expires_at else None,
        }
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users/{user_id}/wallet-adjust")
async def adjust_wallet(
    user_id: uuid.UUID,
    data: AdminWalletAdjustment,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Manually credit or debit a customer's wallet with required reason and audit entry."""
    service = AdminService(db)
    try:
        tx = await service.adjust_wallet(
            user_id=user_id,
            amount_paise=data.amount_paise,
            admin_id=current_admin.id,
            reason=data.reason,
            reference=data.reference,
        )
        await db.commit()
        return {
            "transaction_id": str(tx.id),
            "amount_paise": tx.amount_paise,
            "balance_after_paise": tx.balance_after_paise,
        }
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refund")
async def process_refund(
    data: AdminRefundRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Issue a full or partial refund for a customer transaction."""
    service = AdminService(db)
    try:
        tx = await service.process_refund(
            transaction_id=data.transaction_id,
            amount_paise=data.amount_paise,
            admin_id=current_admin.id,
            reason=data.reason,
        )
        await db.commit()
        return {
            "refund_transaction_id": str(tx.id),
            "amount_paise": tx.amount_paise,
        }
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/config")
async def list_system_config(
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List administrative system configuration entries."""
    res = await db.execute(select(SystemConfig).order_by(SystemConfig.key.asc()))
    configs = list(res.scalars().all())
    return [
        {
            "key": c.key,
            "value": c.value,
            "description": c.description,
            "value_type": c.value_type,
            "updated_at": c.updated_at,
        }
        for c in configs
    ]


@router.put("/config/{key}")
async def update_system_config(
    key: str,
    data: SystemConfigUpdate,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update or create a system configuration setting."""
    service = AdminService(db)
    cfg = await service.set_system_config(
        key=key,
        value=data.value,
        admin_id=current_admin.id,
        description=data.description,
    )
    await db.commit()
    return {"key": cfg.key, "value": cfg.value, "updated_at": cfg.updated_at}


@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Query immutable audit log entries with action and resource filtering."""
    audit_service = AuditService(db)
    logs, total = await audit_service.list_logs(
        skip=skip,
        limit=limit,
        action=action,
        resource_type=resource_type,
    )
    return {
        "items": [
            {
                "id": str(l.id),
                "actor_type": l.actor_type,
                "actor_email": l.actor_email,
                "action": l.action,
                "resource_type": l.resource_type,
                "resource_id": l.resource_id,
                "description": l.description,
                "details_before": l.details_before,
                "details_after": l.details_after,
                "metadata": l.metadata_json,
                "created_at": l.created_at,
            }
            for l in logs
        ],
        "total": total,
    }
